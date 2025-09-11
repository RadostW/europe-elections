# Read README.md in ../data/poland to understand the data better

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
config_path = here / "../data/poland/raw_datasets/metadata/replacement_rules.yaml"

administrative_units = (
    here / "../data/poland/raw_datasets/metadata/administrative_units.csv"
)

files_to_parse = (
    (here / "../data/poland/raw_datasets/powiaty").resolve().glob("poland__*.csv")
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
print("Replacement rules for the party names")
print("")
party_names = sorted(config["party_names"].items(), key=lambda item: item[1])
for party_shortname, group in itertools.groupby(party_names, key=lambda item: item[1]):
    party_longnames = [k for k, _ in group]
    print(f"== {party_shortname} ==")
    for longname in party_longnames:
        print(f"    {longname}")

print("")
print("Parsing raw datasets")
print("")

recognised_column_names = (
    config["column_names"]["eligible_voters"]
    + config["column_names"]["issued_ballots"]
    + config["column_names"]["teryt_code"]
    + list(config["party_names"].keys())
)

for file_path in files_to_parse:
    try:
        print(f"Parsing file: {file_path.name}")
        df = pd.read_csv(file_path)

        pattern = r"(\d{4}_\d{2}_\d{2})"
        match = re.search(pattern, file_path.name)
        if match:
            date_str = match.group(1)
        else:
            raise ValueError(f"No date found in filename: {file_path}")

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

        # harmonising teryt codes
        sample_teryt = df_take["teryt_code"].iloc[0]
        if pd.api.types.is_integer_dtype(sample_teryt):
            if len(str(sample_teryt)) in [5, 6]:
                # t = 20500 or t = 326300
                df_take["teryt_code"] = "T_" + df_take["teryt_code"].astype(str).str[
                    :-2
                ].str.zfill(4)

            elif len(str(sample_teryt)) in [3, 4]:
                # t = 201 or t = 1423
                df_take["teryt_code"] = "T_" + df_take["teryt_code"].astype(
                    str
                ).str.zfill(4)
            else:
                raise ValueError(
                    f"Expected 5 or 6 digit teryt codes, got: {sample_teryt}"
                )
        else:
            raise ValueError(
                f"Expected intiger-like teryt codes, got: {sample_teryt} {type(sample_teryt)}"
            )

        df_take = df_take.rename(columns=config["party_names"])

        # ensure results are ints, fill empty cells with 0
        party_columns = [
            c for c in df_take.columns if c in config["party_names"].values()
        ]
        df_take[party_columns] = df_take[party_columns].fillna(0)

        for col in df_take.columns:
            if col == "teryt_code":
                continue

            series = df_take[col]
            if not pd.api.types.is_integer_dtype(series):
                non_integer_values = series[~series.apply(float.is_integer)].tolist()
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

    except Exception as exc:
        print("\n" * 3)
        print(f"Error while parsing: {file_path}")
        print(f"Exception: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        print("\n" * 3)

        raise ValueError("Parsing error")
