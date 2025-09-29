# Read README.md in ../data/germany to understand the data better

import yaml
import itertools
import pathlib
import pandas as pd
import numpy as np
import re
import traceback

#
# Script configuration
#

here = pathlib.Path(__file__).resolve().parent
config_path = (
    here
    / "../data/germany/raw_datasets/metadata/replacement_rules_kreisen_european.yaml"
)

crosswalk_path = (
    here
    / "../data/germany/raw_datasets/metadata/teritorial_reforms.yaml"
)

files_to_parse = (
    (here / "../data/germany/raw_datasets/kreisen").resolve().glob("ew*_kerg*.csv")
)

#
# Processing
#

with open(config_path.resolve(), "r", encoding="utf-8") as in_file:
    try:
        config = yaml.safe_load(in_file)
    except yaml.YAMLError as exc:
        print(exc)

with open(crosswalk_path.resolve(), "r", encoding="utf-8") as in_file:
    try:
        teritorial_crosswalk = yaml.safe_load(in_file)
    except yaml.YAMLError as exc:
        print(exc)

# renames and mergers only
teritorial_crosswalk_sachsen_2008 = dict()
for record in teritorial_crosswalk["sachsen_2008"]:
    old_code = "A_" + str(record["GKCode_Alt"])[:5]
    new_code = "A_" + str(record["GKCode_Neu"])[:5]
    teritorial_crosswalk_sachsen_2008[old_code] = new_code

# renames and mergers only, splits ignored
teritorial_crosswalk_sachsen_anhalt_2007 = dict()
for record in teritorial_crosswalk["sachsen_anhalt_2007"]:
    if len(record["GKCode_Neu"]) > 1:
        continue
    old_code = "A_" + str(record["GKCode_Alt"])[:5]
    new_code = "A_" + str(record["GKCode_Neu"][0])[:5]
    teritorial_crosswalk_sachsen_anhalt_2007[old_code] = new_code


print("")
print("Parsing raw datasets")
print("")

for file_path in files_to_parse:
    try:
        print(f"Parsing file: {file_path.name}")
        year = int(file_path.name[2:6])

        if year < 1994:
            continue

        #
        # Load and change to wide format
        #

        if year in [2004,1999,1994]:
            df = pd.read_csv(file_path)
        elif year in [2024,2019,2014,2009]:
            df_raw = pd.read_csv(
                file_path, header=[0, 1, 2]  # first 3 rows are headers
            )

            # keep only columns whose top-level name is not 'Unnamed...'
            df_raw = df_raw.loc[
                :, ~df_raw.columns.get_level_values(0).str.startswith("Unnamed")
            ]

            # flatten the multiindex into readable column names
            df_raw.columns = [
                "_".join(
                    [
                        str(x).strip()
                        for x in col
                        if pd.notna(x)
                        and not str(x).startswith("Unnamed")
                        and not str(x).startswith("Stimmen")
                        and not str(x).startswith("Endgültig")
                    ]
                )
                for col in df_raw.columns
            ]

            #df_raw = df_raw[df_raw["gehört zu"] < 50].copy()
            df = df_raw

        else:
            raise NotImplementedError

        #
        # Rename columns and cleanup Kreise codess
        #

        if year <= 2024 and year >= 1994:

            recognised_column_names = (
                config["column_names"]["eligible_voters"]
                + config["column_names"]["issued_ballots"]
                + config["column_names"]["teryt_code"]
                + list(config["choices_names"].keys())
            )

            columns = df.columns
            take_column = [[c, (c in recognised_column_names)] for c in columns]

            for c, v in take_column:
                print(f"{'+' if v else ' '} {c[:20] + ('...' if len(c) > 20 else '')}")

            df_take = df[[c for [c, v] in take_column if v]].copy()

            # extract important columns (eg. eligible_voters)
            for special in config["column_names"].keys():
                t_cols = [
                    c for c in df_take.columns if c in config["column_names"][special]
                ]
                if len(t_cols) != 1:
                    raise ValueError(f"Expected one {special} column, got: {t_cols}")
                df_take = df_take.rename(columns={t_cols[0]: special})

            # harmonise teryt codes
            sample_teryt = df_take["teryt_code"].iloc[0]
            if sample_teryt == "01 0 01":
                pattern = r"^\d{2} \d \d{2}$"
                df_take = df_take[
                    df_take["teryt_code"].astype(str).str.match(pattern, na=False)
                ]  # drop cells describing bundesland results
                df_take["teryt_code"] = "A_" + df_take["teryt_code"].astype(
                    str
                ).str.replace(" ", "")
            elif sample_teryt == 1001.0:
                df_take = df_take[
                    df_take["teryt_code"] > 1000
                ]  # drop cells describing bundesland results
                df_take["teryt_code"] = "A_" + df_take["teryt_code"].astype(int).astype(
                    str
                ).str.zfill(5)
            else:
                raise NotImplementedError

            # Old, croswalk prototype, now defunct
            # df_take["original_teryt_code"] = df_take["teryt_code"].copy()
            # df_take["teryt_code"] = df_take["teryt_code"].replace(teritorial_crosswalk_sachsen_2008)
            # df_take["teryt_code"] = df_take["teryt_code"].replace(teritorial_crosswalk_sachsen_anhalt_2007)

            df_take = df_take.rename(columns=config["choices_names"])

            # ensure results are ints, fill empty cells with 0
            party_columns = [
                c for c in df_take.columns if c in config["choices_names"].values()
            ]
            df_take[party_columns] = df_take[party_columns].fillna(0)

            for col in df_take.columns:
                if col == "teryt_code":
                    continue
                if col == "original_teryt_code":
                    continue

                series = df_take[col]
                if not pd.api.types.is_integer_dtype(series):
                    non_integer_values = series[
                        ~series.apply(float.is_integer)
                    ].tolist()
                    if len(non_integer_values) > 0:
                        raise ValueError(
                            f"Expected non-negative integers, got non-integer values: {non_integer_values} in column '{col}'"
                        )
                    df_take[col] = df_take[col].astype(int)

                negative_values = series[series < 0].tolist()
                if negative_values:
                    raise ValueError(
                        f"Expected non-negative integers, got negative values: {negative_values} in column '{col}'"
                    )

            # sanity check
            totals = df_take[party_columns].sum()
            total_votes = totals.sum()
            percentages = totals / total_votes * 100
            major_parties = percentages[percentages >= 2].sort_values(ascending=False)

            if len(major_parties) == 0:
                print(df.columns)

            date_str = config["year_to_date"][str(year)]
            print(f"Check results: {date_str}")
            # Print results
            for party, pct in major_parties.items():
                print(f"{party[:10]:10} {pct:6.2f}%")

            winner_name, winner_score = list(major_parties.items())[0]
            results_check = config["results_checks"][date_str]
            winner_name_check, winner_score_check = (
                results_check["winner"],
                results_check["result"],
            )
            if winner_name_check != winner_name or not np.isclose(
                winner_score_check, winner_score, atol=0.01
            ):
                raise ValueError(
                    f"Expected {winner_name_check} {winner_score_check}, got: {winner_name} {winner_score}"
                )
            else:
                print("results check OK")                            

            output_path = here / (
                f"../data/germany/harmonised/kreisen/germany__european__{date_str}.csv"
            )
            df_take.to_csv(output_path)
            print("")

    except Exception as exc:
        print("\n" * 3)
        print(f"Error while parsing: {file_path}")
        print(f"Exception: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        print("\n" * 3)

        raise ValueError("Parsing error")
