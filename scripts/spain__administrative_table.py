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

here = pathlib.Path(__file__).resolve().parent

config_path = here / "../data/spain/raw_datasets/metadata/replacement_rules.yaml"
nuts_path = here / "../data/spain/raw_datasets/metadata/nuts_2024_spain.csv"

with open(config_path.resolve(), "r", encoding="utf-8") as in_file:
    try:
        config = yaml.safe_load(in_file)
    except yaml.YAMLError as exc:
        print(exc)

df_nuts = pd.read_csv(nuts_path)

df_nuts_1 = df_nuts[df_nuts["NUTS level"] == 1].copy()
df_nuts_2 = df_nuts[df_nuts["NUTS level"] == 2].copy()
df_nuts_3 = df_nuts[df_nuts["NUTS level"] == 3].copy()

df_nuts_1 = df_nuts_1.rename(
    columns={"NUTS Code": "NUTS 1 Code", "NUTS label": "NUTS 1 name"}
)
df_nuts_2 = df_nuts_2.rename(
    columns={"NUTS Code": "NUTS 2 Code", "NUTS label": "NUTS 2 name"}
)
df_nuts_3 = df_nuts_3.rename(
    columns={"NUTS Code": "NUTS 3 Code", "NUTS label": "NUTS 3 name"}
)

df_nuts_2["NUTS 1 Code"] = df_nuts_2["NUTS 2 Code"].str[:3]
df_nuts_3["NUTS 2 Code"] = df_nuts_3["NUTS 3 Code"].str[:4]

df_merged = pd.merge(
    left=df_nuts_2, right=df_nuts_3, left_on="NUTS 2 Code", right_on="NUTS 2 Code"
)
df_merged = pd.merge(
    left=df_nuts_1, right=df_merged, left_on="NUTS 1 Code", right_on="NUTS 1 Code"
)

df_merged["harmonised_code"] = df_merged["NUTS 3 Code"].map(
    config["nuts2016_to_harmonised_code"]
)
df_merged["harmonised_name"] = df_merged["harmonised_code"].map(config["code_to_name"])

df_merged = df_merged.rename(
    columns={
        "NUTS 3 Code": "nuts3_code",
        "NUTS 1 name": "nuts1_name",
        "NUTS 2 name": "nuts2_name",
        "NUTS 3 name": "nuts3_name",
    }
)

df_merged["nuts_0"] = df_merged["nuts3_code"].str[:2]
df_merged["nuts_1"] = df_merged["nuts3_code"].str[2:3]
df_merged["nuts_2"] = df_merged["nuts3_code"].str[3:4]
df_merged["nuts_3"] = df_merged["nuts3_code"].str[4:]

df_merged = df_merged[
    [
        "harmonised_code",
        "nuts3_code",
        "nuts_0",
        "nuts_1",
        "nuts_2",
        "nuts_3",
        "harmonised_name",
        "nuts3_name",
        "nuts2_name",
        "nuts1_name",
    ]
]


output_file_path = here / "../data/spain/harmonised/provincias/spain__region_data.csv"

# Override values for 3 island regions
#        nuts2_name nuts_3_code            nuts3_name harmonised_code
# 38  Illes Balears       ES531  Eivissa y Formentera            I_07
# 39  Illes Balears       ES532              Mallorca            I_07
# 40  Illes Balears       ES533               Menorca            I_07
# ---
# 52       Canarias       ES703             El Hierro            I_38
# 55       Canarias       ES706             La Gomera            I_38
# 56       Canarias       ES707              La Palma            I_38
# 57       Canarias       ES708             Lanzarote            I_38
# 58       Canarias       ES709              Tenerife            I_38
# ---
# 53       Canarias       ES704         Fuerteventura            I_35
# 54       Canarias       ES705          Gran Canaria            I_35
df_merged = df_merged[~df_merged["harmonised_code"].isin(["I_07", "I_38", "I_35"])]

df_merged = pd.concat(
    [
        df_merged,
        pd.DataFrame(
            {
                "harmonised_code": ["I_07", "I_38", "I_35"],
                "nuts3_code": ["ES53X", "ES70X", "ES70Y"],
                "nuts_0": ["ES", "ES", "ES"],
                "nuts_1": [5, 7, 7],
                "nuts_2": [3, 0, 0],
                "nuts_3": ["X", "X", "Y"],
                "harmonised_name": ["Illes Balears", "Canarias A", "Canarias B"],
                "nuts3_name": ["Illes Balears", "Canarias A", "Canarias B"],
                "nuts2_name": ["Illes Balears", "Canarias A", "Canarias B"],
                "nuts1_name": ["Este", "Canarias", "Canarias"],
            }
        ),
    ]
)

df_merged.to_csv(output_file_path)
