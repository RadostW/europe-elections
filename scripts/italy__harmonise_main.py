# Read README.md in ../data/italy to understand the data better

import italy__harmonise_load_files
import italy__harmonise_standardize
import italy__harmonise_merge_gdf
import italy__harmonise_visualise

import pathlib

import re
import pandas as pd

here = pathlib.Path(__file__).resolve().parent
raw_folder = here / "../data/italy/raw_datasets"
config_path = raw_folder / "metadata/replacement_rules_comunes.yaml"
files_to_parse = sorted(list((raw_folder / "province").resolve().glob("*.csv")))
comune_geodata_path = raw_folder / "metadata" / "comunes_data.geojson"

config = italy__harmonise_load_files.load_config(config_path)

long_dfs = []

code_pairs = []

for file_path in files_to_parse:
    print(f"Parsing file: {file_path.name}")

    pattern = r"^(\d{8})__"
    match = re.search(pattern, file_path.name)
    if match:
        date_str = match.group(1)
    else:
        raise ValueError(f"No date found in filename: {file_path}")

    # if date_str != "20220925":
    #     # WARN: debug handle
    #     continue

    reference_frames = italy__harmonise_load_files.load_reference_gdf(
        comune_geodata_path, date_str
    )
    gdf = reference_frames["geodataframe_at_date"]
    gdf_lax = reference_frames["geodataframe_at_fuzzy_date"]

    if "vaosta" in str(file_path.name).lower():
        continue  # skip for now

    df_raw = italy__harmonise_load_files.load_election(file_path)
    df = italy__harmonise_standardize.standardize_columns(df_raw, config)

    columns_locality = italy__harmonise_standardize.columns_locality.copy()
    columns_neighbourhood = italy__harmonise_standardize.columns_neighbourhood

    df_localities = (
        df[columns_locality]
        .groupby(columns_locality, dropna=False)
        .first()
        .reset_index()
    )

    gdf_date = gdf

    if (
        df_localities["comune_clean"].iloc[0]
        == df_localities["comune_provincia_clean"].iloc[0]
    ):
        match_column = "comune_clean"
        drop_column = "comune_provincia_clean"
    else:
        match_column = "comune_provincia_clean"
        drop_column = "comune_clean"

    columns_locality.remove(drop_column)

    merge_results = italy__harmonise_merge_gdf.merge_with_gdf(
        df_localities.drop(columns=drop_column),
        gdf_date.drop(columns=drop_column),
        columns_neighbourhood,
        match_column,
    )

    matched_gdf = merge_results["matched_gdf"]
    matched_mistakes = merge_results["matched_mistakes"]
    matched_fuzzy = merge_results["matched_fuzzy"]
    matched_very_fuzzy = merge_results["matched_very_fuzzy"]

    # italy__harmonise_visualise.visualise(
    #     matched_mistakes, matched_gdf, columns_neighbourhood
    # )

    matched_gdf = matched_gdf.rename(
        columns={
            "terr_key": "harmonised_code",
            "com_nuts3": "nuts_3_code",
            "name_it": "harmonised_name",
        }
    )

    df_with_codes = pd.merge(
        left=df,
        right=matched_gdf[
            columns_locality + ["harmonised_code", "harmonised_name", "nuts_3_code"]
        ],
        on=columns_locality,
        how="left",
    )

    df_list_votes = df_with_codes.copy()
    df_list_votes = df_list_votes.rename(columns={"list_name": "name"})
    df_list_votes["type"] = 2

    df_eligible_voters = (
        df_with_codes.groupby(columns_locality, dropna=False).first().reset_index()
    .drop(columns="votes")).rename(columns={"eligible_voters": "votes"})
    df_eligible_voters["name"] = "eligible_voters"
    df_eligible_voters["type"] = 0

    df_issued_ballots = (
        df_with_codes.groupby(columns_locality, dropna=False).first().reset_index()
    .drop(columns="votes")).rename(columns={"issued_ballots": "votes"})
    df_issued_ballots["name"] = "issued_ballots"
    df_issued_ballots["type"] = 1

    raw_columns = [
        "harmonised_code",
        "harmonised_name",
        "type",
        "name",
        "votes",
    ]
    standard_columns = [
        "election_date",
        "election_type",
    ] + raw_columns

    # Concatenate all three DataFrames
    df_long = pd.concat(
        [
            df_list_votes[raw_columns],
            df_eligible_voters[raw_columns],
            df_issued_ballots[raw_columns],
        ],
        axis=0,
    ).reset_index()

    df_long["election_date"] = f"{date_str[:4]}_{date_str[4:6]}_{date_str[6:]}"

    if "camera" in file_path.name.lower():
        election_type = "camera"
    elif "europee" in file_path.name.lower():
        election_type = "european"
    else:
        ValueError(f"Unable to guess eleciton type from {file_path.name}")

    df_long["election_type"] = election_type

    # Reorder columns and rows
    df_long = df_long[standard_columns]
    df_long = df_long.sort_values(by=list(df_long.columns))
    df_long = df_long.groupby(
        [
            "election_date",
            "election_type",
            "harmonised_code",
            "harmonised_name",
            "type",
            "name",
        ]
    ).sum().reset_index()

    long_dfs.append(df_long.copy())    

    code_pairs.append(matched_gdf[['harmonised_code','harmonised_name','nuts_3_code']].drop_duplicates())


very_long_df = pd.concat(long_dfs, ignore_index=True)
very_long_output_path = here / (f"../data/italy/harmonised/province/italy.csv")
very_long_df.to_csv(very_long_output_path)

code_pairs_df = pd.concat(code_pairs, ignore_index=True).drop_duplicates()
code_pairs_output_path = here / (f"../data/italy/harmonised/province/italy_harmonised_codes.csv")
code_pairs_df.to_csv(code_pairs_output_path)

