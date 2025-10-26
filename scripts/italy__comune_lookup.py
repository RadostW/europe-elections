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
comunes_path = here / "../data/italy/raw_datasets/metadata/encountered_comune_names.csv"
nuts_2024_path = here / "../data/italy/raw_datasets/metadata/nuts_2024_official.csv"
comune_to_nuts_2024_path = here / "../data/italy/raw_datasets/metadata/Italy-LAU-2024-NUTS-2024.csv"

#
# Processing
#

print("")
print("Parsing raw datasets")
print("")

df_comune = pd.read_csv(
    comunes_path,
    index_col=0,
)

df_nuts_raw = pd.read_csv(
    nuts_2024_path,
)

df_comune_to_nuts_2024 = pd.read_csv(
    comune_to_nuts_2024_path,
)


df_comune["comune_clean"] = [
    re.sub(r"[^A-Za-z ]", "", x.lower()) for x in df_comune["comune"]
]
df_nuts_raw["nuts_clean"] = [
    re.sub(r"[^A-Za-z ]", "", x.lower()) for x in df_nuts_raw["NUTS label"]
]

df_nuts = pd.merge(df_comune_to_nuts_2024,df_nuts_raw,left_on="NUTS 3 CODE",right_on="NUTS Code")

nuts_names = set(df_nuts_raw["nuts_clean"].values)

df_comune["teryt_name"] = df_comune["teryt_name"].replace(
    "Reggio Emilia", "Reggio nell'Emilia"
)

df_comune["official"] = [
    (1 if re.sub(r"[^A-Za-z ]", "", x.lower()) in nuts_names else 0)
    for x in df_comune["teryt_name"]
]

mvt = 0

valid_target_conflicts = []

for x in set(df_comune.comune_clean.values):
    targets = df_comune.query(f'comune_clean == "{x}"')
    if sum(targets["official"].values) == 0:
        print("No valid targets:")
        print(targets)
        print()

    valid_targets = (targets.query("official == 1")["teryt_name"]).drop_duplicates()

    if len(valid_targets) > 1:
        valid_target_conflicts.append("; ".join(sorted(list(valid_targets.values))))
        
        print("Multiple valid targets:")
        print(targets)
        print()

print(f"{mvt=}")
