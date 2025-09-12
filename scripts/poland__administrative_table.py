# Read README.md in ../data/poland to understand the data better

import pathlib
import pandas as pd
import json
import numpy as np

#
# Script configuration
#

here = pathlib.Path(__file__).resolve().parent

admin_file_path = here / "../data/poland/raw_datasets/metadata/administrative_units.csv"

nuts_file_path = (
    here
    / "../data/poland/raw_datasets/metadata/poland__region_id__all_units_levels_0_to_5.json"
)

nuts_id_file_path = (
    here
    / "../data/poland/raw_datasets/metadata/poland__region_id__nuts_coding.csv"
)

#
# Processing
#

df_admin = pd.read_csv(admin_file_path)

# Load region hierarchy JSON
with open(nuts_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)
id_map = {item["id"]: item for item in data}

# Build list of level 5 units with hierarchy
records = []

for item in data:
    if item["level"] == 5:
        record = {"level_5_id": str(item["id"]), "level_5_name": item["name"].strip()}

        current = item
        for level in range(4, 0, -1):
            parent_id = current.get("parentId")
            parent = id_map.get(parent_id)

            if parent and parent["level"] == level:
                record[f"level_{level}_id"] = str(parent["id"])
                record[f"level_{level}_name"] = parent["name"].strip()
                current = parent
            else:
                record[f"level_{level}_id"] = None
                record[f"level_{level}_name"] = None

        records.append(record)

hierarchy_df = pd.DataFrame(records)
# new row as dictionary
new_row = {
    "level_5_id": "030210365000",
    "level_5_name": "Powiat m. Wałbrzych",
    "level_4_id": "030210300000",
    "level_4_name": "PODREGION WAŁBRZYSKI",
    "level_3_id": "030210000000",
    "level_3_name": "REGION DOLNOŚLĄSKIE",
    "level_2_id": "030200000000",
    "level_2_name": "DOLNOŚLĄSKIE",
    "level_1_id": "030000000000",
    "level_1_name": "MAKROREGION POŁUDNIOWO-ZACHODNI",    
}
hierarchy_df = pd.concat(
    [hierarchy_df, pd.DataFrame([new_row])],
    ignore_index=True
)


hierarchy_df["level_5_clean_name"] = hierarchy_df["level_5_name"]

df_woj = df_admin[df_admin["POW"].isna()]
df_pow = df_admin[df_admin["GMI"].isna() & df_admin["POW"].notna()]
df_gmi = df_admin[df_admin["GMI"].notna()]

# Regex: 'Powiat(?: m\.)?' means "Powiat" optionally followed by " m."
split_cols = hierarchy_df["level_5_name"].str.extract(
    r"^(Powiat(?:\s(?:m\.|st\.))*)\s+(.*)$"
)

# Assign new columns
hierarchy_df["prefix"] = split_cols[0]
hierarchy_df["name"] = split_cols[1]


# merge df_pow with df_woj to bring woj name
df_pow_extra = df_pow.merge(
    df_woj[["WOJ", "NAZWA"]],  # select only relevant columns
    on="WOJ",  # join by WOJ id
    how="left",
)

df_pow_extra = df_pow_extra.rename(
    columns={"NAZWA_x": "nazwa_powiatu", "NAZWA_y": "nazwa_wojewodztwa"}
)

hierarchy_df["nazwa_wojewodztwa"] = hierarchy_df["level_2_name"].str.lower()
hierarchy_df["nazwa_powiatu"] = hierarchy_df["name"].str.lower()

hierarchy_df["woj_pow"] = (
    hierarchy_df["nazwa_wojewodztwa"].str.lower()
    + "_"
    + hierarchy_df["nazwa_powiatu"].str.lower()
)

df_pow_extra["woj_pow"] = (
    df_pow_extra["nazwa_wojewodztwa"].str.lower()
    + "_"
    + df_pow_extra["nazwa_powiatu"].str.lower()
)

df_big = df_pow_extra.merge(hierarchy_df, on="woj_pow", how="outer")
df_big = df_big[df_big["nazwa_powiatu_x"].notna()]


df_nuts_id = pd.read_csv(nuts_id_file_path)
df_nuts_id["level_4_name"] = "podregion " + df_nuts_id["nuts_3_name"].str.lower()

df_big["level_4_name"] = df_big["level_4_name"].str.lower()
# df_big = df_big.merge(df_nuts_id,on="level_4_name",how="outer")

df_big = pd.merge(df_big,df_nuts_id,how="outer",on="level_4_name")

df_out = pd.DataFrame()

df_out["teryt"] = (
    "T_"
    + df_big["WOJ"].astype(int).astype(str).str.zfill(2)
    + df_big["POW"].astype(int).astype(str).str.zfill(2)
)
df_out["teryt_woj"] = df_big["WOJ"].astype(int)
df_out["teryt_pow"] = df_big["POW"].astype(int)
df_out["nuts"] = df_big["nuts_3_code"].astype(str)
df_out["nuts_0"] = df_big["nuts_3_code"].astype(str).str[:2]
df_out["nuts_1"] = df_big["nuts_3_code"].astype(str).str[2:3]
df_out["nuts_2"] = df_big["nuts_3_code"].astype(str).str[3:4]
df_out["nuts_3"] = df_big["nuts_3_code"].astype(str).str[4:5]

df_out["pow_name"] = df_big["name"]
df_out["pow_prefix"] = df_big["prefix"].str.lower()
df_out["woj_name"] = df_big["nazwa_wojewodztwa_x"].str.lower()
df_out["woj_prefix"] = "województwo"
df_out["nuts_1_name"] = df_big["level_1_name"].str.lower().str.replace("makroregion ","")
df_out["nuts_1_prefix"] = "makroregion"
df_out["nuts_2_name"] = df_big["level_3_name"].str.lower().str.replace("region ","")
df_out["nuts_2_prefix"] = "region"
df_out["nuts_3_name"] = df_big["level_4_name"].str.lower().str.replace("podregion ","")
df_out["nuts_3_prefix"] = "podregion"

output_file_path = (
    here
    / "../data/poland/harmonised/powiaty/poland__region_data.csv"
)

df_out.to_csv(output_file_path)