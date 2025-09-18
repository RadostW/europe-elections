#
# Bundestag 2025
#

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
    here / "../data/germany/raw_datasets/metadata/replacement_rules_kreisen.yaml"
)

gerda_file_path = here / "../data/germany/raw_datasets/kreisen/federal_cty_harm.csv"

gerda_2025_file_path = here / "../data/germany/raw_datasets/kreisen/federal_muni_harm_25.csv"

#
# Processing
#

with open(config_path.resolve(), "r", encoding="utf-8") as in_file:
    try:
        config = yaml.safe_load(in_file)
    except yaml.YAMLError as exc:
        print(exc)

print("")
print("Parsing raw dataset")
print("")

df = pd.read_csv(gerda_2025_file_path)
df = df[df["election_year"] == 2025]
df = df.rename(columns={"county": "county_code"})

date = "2025_02_23"

recognised_column_names = (
    config["column_names"]["eligible_voters"]
    + config["column_names"]["issued_ballots"]
    + config["column_names"]["teryt_code"]
    + list(config["choices_columns_2025"])
)

columns = df.columns
take_column_nonzero = [
    [c, (c in recognised_column_names) and ((df[c] > 0).any())] for c in columns
]

for c, v in take_column_nonzero:
    print(f"{'+' if v else ' '} {c[:20] + ('...' if len(c) > 20 else '')}")

df_take = df[[c for c, v in take_column_nonzero if v]]

for special in config["column_names"].keys():
    t_cols = [c for c in df_take.columns if c in config["column_names"][special]]
    if len(t_cols) != 1:
        raise ValueError(f"Expected one {special} column, got: {t_cols}")
    df_take = df_take.rename(columns={t_cols[0]: special})

# change values to absolute numbers
for c in df_take.columns:
    if c not in config["choices_columns_2025"]:
        continue

    df_take[c] = df_take[c] * df_take["issued_ballots"]

df_take["teryt_code"] = "A_" + df_take["teryt_code"].astype(int).astype(str).str.zfill(
    5
)

df_take_raw = df_take.copy()
df_take = df_take.fillna(0)
df_take = df_take.groupby('teryt_code', as_index=False).sum()

# sanity check
party_columns = [c for c in df_take.columns if c in config["choices_columns_2025"]]
totals = df_take[party_columns].sum()
total_votes = totals.sum()
percentages = totals / total_votes * 100
major_parties = percentages[percentages >= 2]
# major_parties["cdu_csu"] = major_parties["cdu"] + major_parties["csu"]
major_parties = major_parties.sort_values(ascending=False)

if len(major_parties) == 0:
    print(df.columns)

print(f"Check results: {date}")
# Print results
for party, pct in major_parties.items():
    print(f"{party[:10]:10} {pct:6.2f}%")

winner_name, winner_score = list(major_parties.items())[0]
results_check = config["results_checks"][date]
winner_name_check, winner_score_check = (
    results_check["winner"],
    results_check["result"],
)
if winner_name_check != winner_name or not np.isclose(
    winner_score_check,
    winner_score,
    atol=0.1,  # percentage points
):
    raise ValueError(
        f"Expected {winner_name_check} {winner_score_check}, got: {winner_name} {winner_score}"
    )

output_file_path = (
    here / f"../data/germany/harmonised/kreisen/germany__bundestag__{date}.csv"
)

df_take.to_csv(output_file_path)