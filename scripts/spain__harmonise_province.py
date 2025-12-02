# Read README.md in ../data/spain to understand the data better

import yaml
import itertools
import pathlib
import pandas as pd
import numpy as np
import re
import traceback
import unidecode
import tqdm

tqdm.tqdm.pandas()


def normalize_string(x):
    x = unidecode.unidecode(x).lower().strip()
    return (re.sub(r"[^a-z_ ]", "", x)).strip().replace(" ", "_")

here = pathlib.Path(__file__).resolve().parent

config_path = here / "../data/spain/raw_datasets/metadata/replacement_rules.yaml"

files_to_parse = sorted(
    list((here / "../data/spain/raw_datasets/provincias").resolve().glob("*.csv"))
)

with open(config_path.resolve(), "r", encoding="utf-8") as in_file:
    try:
        config = yaml.safe_load(in_file)
    except yaml.YAMLError as exc:
        print(exc)

long_dfs = []

for file_path in files_to_parse:
    print(f"Parsing file: {file_path.name}")

    pattern = r"^(\d{4})_(\d{2})_\d{2}__"
    date_match = re.search(pattern, file_path.name)
    if date_match:        
        year = date_match.group(1)
        month = date_match.group(2)
    elif "eu_ned" in file_path.name:

        pattern = r"^eu_ned_spain_(\d{4})"
        date_match = re.search(pattern, file_path.name)
        year = date_match.group(1)        

        df = pd.read_csv(file_path)
        df["harmonised_code"] = df["nuts2016"].map(
            config["nuts2016_to_harmonised_code"]
        )
        df["harmonised_name"] = df["harmonised_code"].map(config["code_to_name"])

        print("name mismatches")
        print(
            df.query("regionname!=harmonised_name")[
                ["regionname", "harmonised_name"]
            ].drop_duplicates()
        )

        df_votes = df[
            ["harmonised_code", "harmonised_name", "party_abbreviation", "partyvote"]
        ].copy().rename(columns={"party_abbreviation": "name", "partyvote": "votes"})

        df_votes["name"] =  df_votes["name"].map(normalize_string)
        
        df_eligible = df.groupby("nuts2016").first()[
            ["harmonised_code", "harmonised_name", "electorate"]    
        ].copy().rename(columns={"electorate":"votes"})
        df_eligible["name"] = "eligible_voters"
        
        df_issued_ballots = df.groupby("nuts2016").first()[
            ["harmonised_code", "harmonised_name", "totalvote"]    
        ].copy().rename(columns={"totalvote":"votes"})
        df_issued_ballots["name"] = "issued_ballots"
        
        df_long = pd.concat([df_votes,df_eligible,df_issued_ballots])
                
        # Add `type` column
        df_long["type"] = (
            df_long["name"]
            .map({"eligible_voters": 0, "issued_ballots": 1})
            .fillna(2)
            .astype(int)
        )

        election_date = config["year_to_date"][year]
        election_type = 'european'        
    else:
        raise ValueError(f"No date found in filename: {file_path}")

    if "eu_ned" not in file_path.name:

        df = pd.read_csv(
            file_path,
            skiprows=3,  # Skip the first 3 description rows
            header=[0, 1, 2],  # Use the next 3 rows as column headers
        )

        df.columns = [
            "_".join(
                [
                    str(c)
                    for c in col
                    if not str(c).startswith("Unnamed") and str(c).strip() != ""
                ]
            )
            for col in df.columns
        ]

        keep_cols = list(config["column_names"].keys())
        voto_cols = [c for c in df.columns if c.endswith("Votos")]

        # Combine and subset
        df = df[keep_cols + voto_cols]

        df = df.rename(columns=config["column_names"])

        df.columns = [
            c.split("_")[-2] if c.endswith("_Votos") else c for c in df.columns
        ]

        columns = df.columns
        normalized_columns = [normalize_string(x) for x in columns]

        duplicates = [
            name for name in normalized_columns if normalized_columns.count(name) > 1
        ]
        duplicates = list(set(duplicates))

        if duplicates:
            print("Found duplicates after normalization:\n")
            for dup in duplicates:
                originals = [
                    orig
                    for orig, norm in zip(columns, normalized_columns)
                    if norm == dup
                ]
                print(f"Normalized: {dup}\nOriginals: {originals}\n")
            raise ValueError

        df.columns = normalized_columns
        party_columns = [
            c for c in df.columns if c not in config["column_names"].values()
        ]

        # remove summary rows from the end of dataframe
        df = df[df["harmonised_name"] != "Total"]
        df = df[df["harmonised_name"] != "España"]
        df = df[df["harmonised_name"].notna()]

        df_long = df.melt(
            id_vars=["harmonised_code", "harmonised_name"],
            var_name="name",
            value_name="votes",
        )

        # Add `type` column
        df_long["type"] = (
            df_long["name"]
            .map({"eligible_voters": 0, "issued_ballots": 1})
            .fillna(2)
            .astype(int)
        )

        if "congresso" in file_path.name:
            election_type = "congresso"
        elif "european" in file_path.name:
            election_type = "european"
        else:
            raise ValueError("Unknown election type")

        election_date = config["year_month_to_date"][f"{year}_{month}"]

        # Reformat harmonised_code
        df_long["harmonised_code"] = "I_" + (
            df_long["harmonised_code"].astype(int).astype(str).str.zfill(2)
        )

    # Add metadata columns
    df_long["election_date"] = election_date
    df_long["election_type"] = election_type
    
    # Reorder columns and rows
    df_long = df_long[
        [
            "election_date",
            "election_type",
            "harmonised_code",
            "harmonised_name",
            "type",
            "name",
            "votes",
        ]
    ]
    df_long = df_long.sort_values(
        by=["election_date", "election_type", "harmonised_code", "type"],
        ascending=[True, True, True, True],
    ).reset_index(drop=True)

    df_parties = df_long[df_long["type"] == 2].copy()
    df_issued_ballots = df_long[df_long["type"] == 1].copy()
    party_totals = df_parties.groupby("name")["votes"].sum()

    # wikipedia includes blanks in calculations but not spoilt ballots
    total_votes = party_totals.sum()
    # total_votes = df_issued_ballots['votes'].sum()

    party_pct = (party_totals / total_votes * 100).sort_values(ascending=False)

    major_parties = party_pct.head(10).to_dict()

    date_string = df_long["election_date"].iloc[0]
    election_type = df_long["election_type"].iloc[0]
    print(f"Check results: {date_string}")
    for party, pct in major_parties.items():
        print(f"{party[:10]:10} {pct:6.2f}%")

    winner_name, winner_score = list(major_parties.items())[0]

    results_check = config["results_checks"][date_string]
    winner_name_check, winner_score_check = (
        results_check["winner"],
        results_check["result"],
    )

    tolerance = (
        1.0  # wikipedia / code mismatch of 'total votes' leads to slight differences
    )

    if winner_name_check != winner_name or not np.isclose(
        winner_score_check, winner_score, atol=tolerance
    ):
        if (
            date_string == "2013_02_24"
            and np.isclose(winner_score_check, winner_score, atol=tolerance)
            and winner_name in ["pd", "m5s"]
        ):
            # almost tied election pd-m5s
            print("results check OK")
        else:
            raise ValueError(
                f"Expected {winner_name_check} {winner_score_check}, got: {winner_name} {winner_score}"
            )
    else:
        print("results check OK")

    output_path = here / (
        f"../data/italy/harmonised/province/italy__{election_type}__{date_string}.csv"
    )
    df_long.to_csv(output_path)

    long_dfs.append(df_long.copy())

very_long_df = pd.concat(long_dfs, ignore_index=True)
very_long_df["harmonised_name"] = very_long_df["harmonised_code"].map(
    config["code_to_name"]
)

very_long_output_path = here / (f"../data/spain/harmonised/provincias/spain.csv")
very_long_df.to_csv(very_long_output_path)
