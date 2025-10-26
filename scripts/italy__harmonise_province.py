# Read README.md in ../data/italy to understand the data better

import yaml
import itertools
import pathlib
import pandas as pd
import numpy as np
import re
import traceback
import unidecode

#
# Script configuration
#

here = pathlib.Path(__file__).resolve().parent
config_path = (
    here / "../data/italy/raw_datasets/metadata/replacement_rules_province.yaml"
)

metadata = here / "../data/italy/raw_datasets/metadata/Elenco-comuni-italiani.csv"

files_to_parse = list(
    (here / "../data/italy/raw_datasets/province").resolve().glob("*.csv")
)

#
# Processing
#

with open(config_path.resolve(), "r", encoding="utf-8") as in_file:
    try:
        config = yaml.safe_load(in_file)
    except yaml.YAMLError as exc:
        print(exc)

print("")
print("Parsing raw datasets")
print("")
print([file_path.name for file_path in files_to_parse])

recognised_column_names = (
    config["column_names"]["eligible_voters"]
    + config["column_names"]["issued_ballots"]
    + config["column_names"]["teryt_code"]
    + config["column_names"]["votes"]
    + config["column_names"]["list_name"]
    + config["column_names"]["comune"]
)

df_metadata = pd.read_csv(
    metadata, sep=";", encoding="cp1252"  # or "cp1252" (Windows Western European ANSI)
)

rename_dict = {
    "Denominazione dell'Unità territoriale sovracomunale \n(valida a fini statistici)": "province_name",
    "Codice dell'Unità territoriale sovracomunale \n(valida a fini statistici)": "istat_code",
}

# Rename columns
df_metadata = df_metadata.rename(columns=rename_dict)
df_provinces = df_metadata[["province_name", "istat_code"]].copy()
df_provinces = df_provinces.drop_duplicates(subset="province_name")

province_to_istat = {}
norm_name_to_name = {}
for name, code in zip(df_provinces["province_name"], df_provinces["istat_code"]):
    clean_name = name.split("/")[0].strip()
    clean_name = unidecode.unidecode(clean_name)
    clean_code = f"I_{int(code):03d}"
    province_to_istat[clean_name] = clean_code

    norm_name = re.sub(r"[^A-Za-z]", "", clean_name).lower()
    norm_name_to_name[norm_name] = clean_name

norm_name_to_name["mediocampidano"] = "Medio Campidano"
province_to_istat["Medio Campidano"] = "I_106"
norm_name_to_name["carboniaiglesias"] = "Carbonia-Iglesias"
province_to_istat["Carbonia-Iglesias"] = "I_107"
norm_name_to_name["ogliastra"] = "Ogliastra"
province_to_istat["Ogliastra"] = "I_105"
norm_name_to_name["olbiatempio"] = "Olbia-Tempio"
province_to_istat["Olbia-Tempio"] = "I_104"
norm_name_to_name["reggioemilia"] = "Reggio Emilia"
province_to_istat["Reggio Emilia"] = "I_035"
norm_name_to_name["monzaedellabrianza"] = "Monza e della Brianza"
province_to_istat["Monza e della Brianza"] = "I_108"

norm_name_to_name["carboniaiglesias"] = "Carbonia-Iglesias"
province_to_istat["Carbonia-Iglesias"] = "I_107"

# aliases
norm_name_to_name["aosta"] = "Valle d'Aosta"
norm_name_to_name["monza"] = "Monza e della Brianza"
norm_name_to_name["carboniaigles"] = "Carbonia-Iglesias"

comune_names_dfs = []

for file_path in files_to_parse:
    try:
        print(f"Parsing file: {file_path.name}")

        pattern = r"^(\d{8})__"
        match = re.search(pattern, file_path.name)
        if match:
            date_str = match.group(1)
        else:
            raise ValueError(f"No date found in filename: {file_path}")

        # print(f"{date_str=}")
        if date_str in [
            "19990613",
            "20080413",
            "20090607",
            "20130224",
            "20140525",
        ]:
            df = pd.read_csv(
                file_path,
                sep=";",
            )
        elif date_str in [
            "20040612",
            "20060409",
            "20190526",
            "20240609",
        ]:
            df = pd.read_csv(
                file_path,
                sep=";",
                encoding="cp1252",
            )
        elif date_str in [
            "19960421",
            "20010513",
            "20180304",
            "20220925",
        ]:
            continue  # province data missing - fix pending
        else:
            raise ValueError(f"Unrecognised date {date_str}")

        if "vaosta" in file_path.name:
            # vaosta is a single province
            df["PROVINCIA"] = "Valle d'Aosta"

        columns = df.columns
        take_column = [[c, (c in recognised_column_names)] for c in columns]

        for c, v in take_column:
            print(f"{'+' if v else ' '} {c[:20] + ('...' if len(c) > 20 else '')}")

        df_take = df[[c for [c, v] in take_column if v]]

        # extract important columns (eg. eligible_voters)
        for special in config["column_names"].keys():
            t_cols = [
                c for c in df_take.columns if c in config["column_names"][special]
            ]
            if len(t_cols) != 1:
                raise ValueError(f"Expected one {special} column, got: {t_cols}")
            df_take = df_take.rename(columns={t_cols[0]: special})

        df_take["teryt_name"] = df_take["teryt_code"].copy()

        def normalize_name(name: str) -> str:
            name = unidecode.unidecode(str(name))
            name = re.sub(r"[^A-Za-z]", "", name).lower()
            return name

        df_take["teryt_name_norm"] = df_take["teryt_name"].apply(normalize_name)

        missing_keys = set(df_take["teryt_name_norm"].unique()) - set(
            norm_name_to_name.keys()
        )
        if missing_keys:
            raise KeyError(
                f"The following normalized names are missing in norm_name_to_name: {missing_keys}"
            )

        df_take["teryt_name"] = df_take["teryt_name_norm"].map(norm_name_to_name)
        df_take["teryt_code"] = df_take["teryt_name"].map(province_to_istat)
        df_take = df_take.drop(columns=["teryt_name_norm"])

        comune_names_dfs.append(
            df_take[["comune", "teryt_name", "teryt_code"]]
            .drop_duplicates()
            .copy()
            .reset_index(drop=True)
        )

        # Aggregate votes by list_name and teryt_code
        df_votes = df_take.groupby(
            ["teryt_code", "teryt_name", "list_name"], as_index=False
        )["votes"].sum()

        # Deduplicate per comune within each province
        df_comune = df_take.groupby(["teryt_code", "comune"], as_index=False).first()[
            ["teryt_code", "comune", "eligible_voters", "issued_ballots"]
        ]

        # Step 2: sum eligible_voters and issued_ballots at province level
        df_meta = df_comune.groupby("teryt_code", as_index=False).agg(
            {"eligible_voters": "sum", "issued_ballots": "sum"}
        )

        # Optional: add teryt_name (take first name per province)
        df_meta["teryt_name"] = (
            df_take.groupby("teryt_code")["teryt_name"].first().values
        )

        # Step 3: melt into long format
        df_meta_long = pd.melt(
            df_meta,
            id_vars=["teryt_code", "teryt_name"],
            value_vars=["eligible_voters", "issued_ballots"],
            var_name="name",
            value_name="votes",
        )

        # Assign type codes for eligible_voters (0) and issued_ballots (1)
        df_meta_long["type"] = df_meta_long["name"].map(
            {"eligible_voters": 0, "issued_ballots": 1}
        )

        # Prepare votes for lists, type=2
        df_votes["type"] = 2
        df_votes = df_votes.rename(columns={"list_name": "name"})

        # Combine meta and votes
        df_long = pd.concat(
            [
                df_meta_long,
                df_votes[["teryt_code", "teryt_name", "type", "name", "votes"]],
            ],
            ignore_index=True,
        )

        # Add extra columns (fill with placeholders or constants)
        df_long["election_date"] = f"{date_str[:4]}_{date_str[4:6]}_{date_str[6:]}"

        if "camera" in file_path.name:
            election_type = "camera"
        elif "europee" in file_path.name:
            election_type = "european"
        else:
            ValueError(f"Unable to guess eleciton type from {file_path.name}")

        df_long["election_type"] = election_type
        df_long["harmonised_code"] = df_long["teryt_code"]  # or use a mapping if needed
        df_long["harmonised_name"] = df_long["teryt_name"]

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

        choices_map = config["choices_names"]
        mask = df_long["type"] == 2
        names_to_check = df_long["name"][mask].unique()
        missing = set(names_to_check) - set(choices_map.keys())
        if missing:
            print("Missing values in choices_names:")
            print(sorted(list(missing)))

            print("All values in choices_names:")
            print(sorted(set(names_to_check)))

            raise KeyError(f"Missing values in choices_names.")

        mapped = df_long["name"].map(choices_map)
        df_long["name"] = df_long["name"].where(~mask, mapped)

        df_long = df_long.sort_values(
            by=["election_date", "election_type", "harmonised_code", "type"],
            ascending=[True, True, True, True],
        ).reset_index(drop=True)

        # sanity check

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

        if "aosta" not in file_path.name:
            if winner_name_check != winner_name or not np.isclose(
                winner_score_check, winner_score, atol=0.1
            ):
                raise ValueError(
                    f"Expected {winner_name_check} {winner_score_check}, got: {winner_name} {winner_score}"
                )
            else:
                print("results check OK")

        output_path = here / (
            f"../data/italy/harmonised/province/italy__{election_type}__{date_string}.csv"
        )
        df_long.to_csv(output_path)

    except Exception as exc:
        print("\n" * 3)
        print(f"Error while parsing: {file_path}")
        print(f"Exception: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        print("\n" * 3)

        raise ValueError("Parsing error")

df_comune_names = pd.concat(
            comune_names_dfs,
            ignore_index=True,
        )

df_comune_names["comune"] = df_comune_names["comune"].str.strip()
df_comune_names = df_comune_names.drop_duplicates().sort_values(by="comune").reset_index(drop=True)

df_comune_names.to_csv("comune_names.csv")