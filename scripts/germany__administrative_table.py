# Read README.md in ../data/germany to understand the data better

import pathlib
import pandas as pd
import json
import numpy as np

#
# Script configuration
#

here = pathlib.Path(__file__).resolve().parent

croswalks_file = (
    here / "../data/germany/raw_datasets/metadata/germany__cty_crosswalks.csv"
)

wikipedia_file = (
    here / "../data/germany/raw_datasets/metadata/germany__wikipedia_nuts_names.csv"
)

lookup_file = (
    here
    / "../data/germany/raw_datasets/metadata/germany__Regionen_20DE_20NUTS-3_20KGS.csv"
)

raw_file = here / "../data/germany/raw_datasets/kreisen/federal_cty_harm.csv"

#
# Processing
#

df_admin = pd.read_csv(croswalks_file)
df_admin = df_admin.sort_values(["county_code", "year"]).drop_duplicates(
    "county_code", keep="last"
)

df_wikipedia = pd.read_csv(wikipedia_file)
#df_wikipedia = df_wikipedia.fillna(method="ffill")
df_wikipedia = df_wikipedia.ffill()

df_lookup_file = pd.read_csv(lookup_file)

df_merge_a = pd.merge(
    df_wikipedia, df_lookup_file, how="outer", left_on="Code.2", right_on="NUTS-3"
)
df_merge_b = pd.merge(
    df_merge_a, df_admin, how="outer", left_on="KGS", right_on="county_code"
)

# df_raw = pd.read_csv(raw_file)
# relevant_kreise = df_raw["county_code"].unique()

df_merge_c = df_merge_b
# df_merge_c = df_merge_b[df_merge_b["county_code"].isin(relevant_kreise)]
df_big = df_merge_c.copy()

df_out = pd.DataFrame()

df_big["ags"] = "A_" + df_big["county_code"].astype(int).astype(str).str.zfill(5)

df_out["ags"] = df_big["ags"]
df_out["ags_bundesland"] = df_big["ags"].str[2:4]
df_out["ags_bezirke"] = df_big["ags"].str[4:5]
df_out["ags_kreis"] = df_big["ags"].str[5:]

df_out["nuts"] = df_big["NUTS-3"].astype(str)
df_out["nuts_0"] = df_big["NUTS-3"].astype(str).str[:2]
df_out["nuts_1"] = df_big["NUTS-3"].astype(str).str[2:3]
df_out["nuts_2"] = df_big["NUTS-3"].astype(str).str[3:4]
df_out["nuts_3"] = df_big["NUTS-3"].astype(str).str[4:5]

df_out[["kreis_name", "kreis_name_extra"]] = (
    df_big["county_name"].str.split(",", n=1, expand=True).apply(lambda x: x.str.strip())
)
df_out["kreis_name_extra"] = df_out["kreis_name_extra"].fillna("")

df_out["bezirke_name"] = df_big["NUTS 2"]
df_out["bundesland_name"] = df_big["NUTS 1"]

df_out["nuts_1_name"] = df_big["NUTS 1"]
df_out["nuts_2_name"] = df_big["NUTS 2"]
df_out["nuts_3_name"] = df_big["NUTS 3"]

output_file_path = here / "../data/germany/harmonised/kreisen/germany__region_data.csv"

df_out.to_csv(output_file_path)
