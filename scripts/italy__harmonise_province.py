# Read README.md in ../data/italy to understand the data better

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

here = pathlib.Path(__file__).resolve().parent

config_path = (
    here / "../data/italy/raw_datasets/metadata/replacement_rules_comunes.yaml"
)

files_to_parse = sorted(
    list((here / "../data/italy/raw_datasets/province").resolve().glob("*.csv"))
)

nuts_2024_path = here / "../data/italy/raw_datasets/metadata/nuts_2024_official.csv"
comune_to_nuts_2024_path = (
    here / "../data/italy/raw_datasets/metadata/Italy-LAU-2024-NUTS-2024.csv"
)

df_nuts_raw = pd.read_csv(
    nuts_2024_path,
)

df_comune_to_nuts_2024 = pd.read_csv(
    comune_to_nuts_2024_path,
)

variazioni_path = (
    here / "../data/italy/raw_datasets/metadata/variazioni_amministrative.csv"
)
df_variazioni = pd.read_csv(
    variazioni_path,
)


@pd.api.extensions.register_series_accessor("normalize_string")
class NormalizeStringAccessor:
    def __init__(self, s):
        self._obj = s

    def __call__(self):
        return (
            self._obj.astype(str)
            .map(unidecode.unidecode)
            .str.lower()
            .str.replace(r"[^a-z ]", "", regex=True)
            .str.strip()
        )


df_nuts_raw["nuts_clean"] = df_nuts_raw["NUTS label"].normalize_string()

df_nuts = pd.merge(
    df_comune_to_nuts_2024, df_nuts_raw, left_on="NUTS 3 CODE", right_on="NUTS Code"
)

df_nuts["comune_clean"] = df_nuts["LAU NAME LATIN"].normalize_string()

with open(config_path.resolve(), "r", encoding="utf-8") as in_file:
    try:
        config = yaml.safe_load(in_file)
    except yaml.YAMLError as exc:
        print(exc)

long_dfs = []

for file_path in files_to_parse:
    print(f"Parsing file: {file_path.name}")

    pattern = r"^(\d{8})__"
    match = re.search(pattern, file_path.name)
    if match:
        date_str = match.group(1)
    else:
        raise ValueError(f"No date found in filename: {file_path}")

    # print(f"{date_str=}")
    if date_str in [
        "19960421",
        "19990613",
        "20010513",
        "20080413",
        "20090607",
        "20130224",
        "20140525",
        "20220925",
    ]:
        df = pd.read_csv(
            file_path,
            sep=";",
        )
    elif date_str in [
        "20040612",
        "20060409",
        "20180304",
        "20190526",
        "20240609",
    ]:
        df = pd.read_csv(
            file_path,
            sep=";",
            encoding="cp1252",
        )
    elif date_str in []:
        continue  # province data missing - fix pending
    else:
        raise ValueError(f"Unrecognised date {date_str}")

    if date_str in ["20010513"]:
        # special treatment of 'comunes' which are parts of comunes
        mask = df["COMUNE"].str.contains(" - ", na=False)
        df.loc[mask, "COMUNE"] = df.loc[mask, "COMUNE"].str.partition(" - ")[0]

        df["COMUNE"] = df["COMUNE"].replace(
            {
                "Roma centro": "Roma",
                "Verona Est": "Verona",
                "Messina centro storico": "Messina",
                "Perugia centro": "Perugia",
                "Foggia centro": "Foggia",
                "Verona Ovest": "Verona",
                "Trieste centro": "Trieste",
            }
        )

    if "vaosta" in str(file_path.name).lower():
        continue

    if date_str in ["20140525", "20180304", "20190526", "20220925"]:
        # special treatment of 'comunes' which are named bilingually
        mask = df["COMUNE"].str.contains("/", na=False)
        df.loc[mask, "COMUNE"] = df.loc[mask, "COMUNE"].str.partition("/")[0]

    if date_str in ["20240609"]:
        # special treatment of 'comunes' which are named bilingually
        mask = df["DESCCOMUNE"].str.contains("/", na=False)
        df.loc[mask, "DESCCOMUNE"] = df.loc[mask, "DESCCOMUNE"].str.partition("/")[0]

    columns = df.columns

    for c in columns:
        is_target = False
        target_name = ""
        for key, targets in config["column_names"].items():
            if c in targets:
                is_target = True
                target_name = key
                df = df.rename(columns={c: target_name})

        print(
            f"{'+' if is_target else ' '} {c[:20].ljust(20) + ('...' if len(c) > 20 else '   ')} -> {target_name}"
        )

    df["comune_clean"] = df["comune"].normalize_string()

    nuts_comunes = set(df_nuts["comune_clean"])
    nuts_comunes_no_spaces = set(re.sub(r" ", "", c) for c in nuts_comunes)

    if not "provincia" in df.columns:
        df["provincia"] = "unknown"

    # Step 1. Strict match on comune_clean + provincia
    df["provincia"] = df["provincia"].normalize_string()

    for col in ["comune_clean", "provincia"]:
        df[col] = df[col].astype("category")

    for col in ["comune_clean", "nuts_clean"]:
        df_nuts[col] = df_nuts[col].astype("category")

    df_with_nuts = pd.merge(
        df,
        df_nuts,
        left_on=["comune_clean", "provincia"],
        right_on=["comune_clean", "nuts_clean"],
        how="left",
        # suffixes=("", "_nuts")
    )
    df_with_nuts.loc[df_with_nuts["NUTS Code"].notna(), "match_type"] = "strict"

    # Step 2. Match remaining rows only on comune_clean
    unmatched = df[df_with_nuts["NUTS Code"].isna()].copy()
    matched_name = pd.merge(
        unmatched,
        df_nuts,
        on="comune_clean",
        how="left",
        # suffixes=("", "_nuts")
    )
    matched_name.loc[matched_name["nuts_clean"].notna(), "match_type"] = "name"

    # Combine results carefully — only update where matches were found
    df_with_nuts.update(matched_name[matched_name["nuts_clean"].notna()])

    # Step 3. Fill remaining unmatched rows by "neighbour" (most common nuts_clean per group)
    possible_group_cols = [
        "provincia",
        "circoscrizione",
        "regione",
        "collegio",
        "collegio_plurinominale",
        "collegio_uninominale",
    ]
    group_cols = [c for c in df.columns if c in possible_group_cols]

    # Build a compact key string for grouping and mapping
    df_with_nuts["_group_key"] = (
        df_with_nuts[group_cols].astype(str).agg("|".join, axis=1)
    )

    # Compute most common nuts_clean per group (from already matched rows)
    most_common_nuts_name = (
        df_with_nuts.dropna(subset=["nuts_clean"])
        .groupby("_group_key")["nuts_clean"]
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)
        .to_dict()
    )
    name_to_code = (
        df_with_nuts[["nuts_clean", "NUTS Code"]]
        .drop_duplicates()
        .dropna()
        .set_index("nuts_clean")
        .to_dict()["NUTS Code"]
    )

    # Fill missing nuts_clean for unmatched rows using the mapping
    mask = df_with_nuts["nuts_clean"].isna()
    df_with_nuts.loc[mask, "nuts_clean"] = df_with_nuts.loc[mask, "_group_key"].map(
        most_common_nuts_name
    )
    df_with_nuts.loc[mask, "NUTS Code"] = df_with_nuts.loc[mask, "nuts_clean"].map(
        name_to_code
    )

    # Mark as 'neighbour' only the rows that were previously unmatched but now filled
    df_with_nuts.loc[
        df_with_nuts["match_type"].isna() & df_with_nuts["nuts_clean"].notna(),
        "match_type",
    ] = "neighbour"

    # Clean up helper column
    # df_with_nuts.drop(columns="_group_key", inplace=True)

    # Step 4. Everything else = fail
    df_with_nuts["match_type"] = df_with_nuts["match_type"].fillna("fail")

    # Step 5. Print proportions of each match type
    print("")
    print("Matched with NUTS:")
    vote_proportions = (
        df_with_nuts.groupby("match_type")["votes"].sum() / df_with_nuts["votes"].sum()
    )
    print(vote_proportions)
    print("")

    if "fail" in vote_proportions.keys() and vote_proportions["fail"] > 0.001:
        print("Too many failed matches")
        raise ValueError

    # Reshape to long format and clena names
    df_with_nuts = df_with_nuts.rename(
        columns={"NUTS Code": "harmonised_code", "nuts_clean": "harmonised_name"}
    )

    for col in ["comune_clean", "provincia", "harmonised_name", "harmonised_code"]:
        df_with_nuts[col] = df_with_nuts[col].astype("str")

    if len(df_with_nuts[df_with_nuts.harmonised_code.isna()]) > 0:
        raise ValueError("all rows should have codes")
    if len(df_with_nuts[df_with_nuts.harmonised_code == "nan"]) > 0:
        raise ValueError("all rows should have codes")

    df_list_votes = df_with_nuts.groupby(
        ["harmonised_code", "harmonised_name", "list_name"], as_index=False
    )["votes"].sum()
    df_list_votes = df_list_votes.rename(columns={"list_name": "name"})
    df_list_votes["type"] = 2

    df_eligible_voters = df_with_nuts.groupby(
        group_cols
        + ["harmonised_code", "harmonised_name", "comune", "eligible_voters"],
        as_index=False,
    ).first()
    df_eligible_voters = df_eligible_voters[
        ["harmonised_code", "harmonised_name", "eligible_voters"]
    ]
    df_eligible_voters = df_eligible_voters.rename(columns={"eligible_voters": "votes"})
    df_eligible_voters = df_eligible_voters.groupby(
        ["harmonised_code", "harmonised_name"], as_index=False
    ).sum()
    df_eligible_voters["name"] = "eligible_voters"
    df_eligible_voters["type"] = 0

    df_issued_ballots = df_with_nuts.groupby(
        group_cols + ["harmonised_code", "harmonised_name", "comune", "issued_ballots"],
        as_index=False,
    ).first()
    df_issued_ballots = df_issued_ballots[
        ["harmonised_code", "harmonised_name", "issued_ballots"]
    ]
    df_issued_ballots = df_issued_ballots.rename(columns={"issued_ballots": "votes"})
    df_issued_ballots = df_issued_ballots.groupby(
        ["harmonised_code", "harmonised_name"], as_index=False
    ).sum()
    df_issued_ballots["name"] = "issued_ballots"
    df_issued_ballots["type"] = 1

    # Concatenate all three DataFrames
    df_long = pd.concat(
        [df_list_votes, df_eligible_voters, df_issued_ballots],
        axis=0,
        ignore_index=True,  # optional, resets the index
    )

    df_long["election_date"] = f"{date_str[:4]}_{date_str[4:6]}_{date_str[6:]}"

    if "camera" in file_path.name.lower():
        election_type = "camera"
    elif "europee" in file_path.name.lower():
        election_type = "european"
    else:
        ValueError(f"Unable to guess eleciton type from {file_path.name}")

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

    # party names to abbreviations
    recognised_party_names = set(config["choices_names"].keys())
    present_names = set(df_long["name"])

    missing_names = present_names - (
        recognised_party_names | set(["issued_ballots", "eligible_voters"])
    )

    if missing_names:
        print("missing names:")
        print(missing_names)
        print("")
        print("all names:")
        print(present_names - set(["issued_ballots", "eligible_voters"]))
        raise ValueError

    df_long["name"] = df_long["name"].replace(config["choices_names"])

    df_parties = df_long[df_long["type"] == 2].copy()
    party_totals = df_parties.groupby("name")["votes"].sum()
    total_votes = party_totals.sum()
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

    tolerance = 1.0  # (= 1 percentage point) aosta results missing

    if "aosta" not in file_path.name:
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
very_long_output_path = here / (f"../data/italy/harmonised/province/italy.csv")
very_long_df.to_csv(very_long_output_path)
