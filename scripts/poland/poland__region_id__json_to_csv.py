import json
import pandas as pd
import csv
import re

# Paths
json_path = (
    "../../data/poland/raw_datasets/poland__region_id__all_units_levels_0_to_5.json"
)
nuts_csv_path = "../../data/poland/raw_datasets/poland__region_id__nuts_coding.csv"
teryt_csv_path = "../../data/poland/raw_datasets/poland__region_id__teryt_coding.csv"
teryt_voivodship_csv_path = (
    "../../data/poland/raw_datasets/poland__region_id__teryt_coding_voivodships.csv"
)

# Load region hierarchy JSON
with open(json_path, "r", encoding="utf-8") as f:
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

# -------------------------------------------------------------------

# Load NUTS3 codes
nuts_df = pd.read_csv(nuts_csv_path)
nuts_df["nuts_3_name"] = nuts_df["nuts_3_name"].str.strip()
nuts_df["nuts_3_code"] = nuts_df["nuts_3_code"].str.strip()

# Prepare both sides for matching
hierarchy_df["match_key"] = (
    hierarchy_df["level_4_name"].str.replace("PODREGION ", "", regex=False).str.lower()
)
nuts_df["match_key"] = nuts_df["nuts_3_name"].str.strip().str.lower()

assert (
    hierarchy_df["match_key"].isin(nuts_df["match_key"]).all()
), "There are match_key values in df not found in nuts_df"
assert (
    nuts_df["match_key"].isin(hierarchy_df["match_key"]).all()
), "There are match_key values in nuts_df not found in df"

# Merge on match_key
hierarchy_df = hierarchy_df.merge(
    nuts_df[["match_key", "nuts_3_code", "nuts_3_name"]], how="left", on="match_key"
)

# Drop match_key (was only for internal merge logic)
hierarchy_df.drop(columns=["match_key"], inplace=True)

# -------------------------------------------------------------------

# Load TERYT codings
teryt_powiat_df = pd.read_csv(teryt_csv_path)
teryt_voivodship_df = pd.read_csv(teryt_voivodship_csv_path)

teryt_df_raw = teryt_voivodship_df.merge(
    teryt_powiat_df, how="inner", on="WOJ", suffixes=("_woj", "_pow")
)

teryt_df = (
    teryt_df_raw[
        ["WOJ", "POW_pow", "NAZWA_woj", "NAZWA_DOD_woj", "NAZWA_pow", "NAZWA_DOD_pow"]
    ]
    .rename(columns={"POW_pow": "POW", "NAZWA_DOD_pow": "NAZWA_pow_DOD"})
    .rename(
        columns={
            "WOJ": "voivodship_id",
            "POW": "powiat_id",
            "NAZWA_woj": "voivodship_name",
            "NAZWA_DOD_woj": "voivodship_name_extra",
            "NAZWA_pow": "powiat_name",
            "NAZWA_pow_DOD": "powiat_name_extra",
        }
    )
)
teryt_df["teryt_code"] = (
    "T_"
    + teryt_df["voivodship_id"].astype(str).str.zfill(2)
    + teryt_df["powiat_id"].astype(str).str.zfill(2)
)

teryt_df["match_key"] = (
    teryt_df["powiat_name"].astype(str) + " (" + teryt_df["voivodship_name"] + ")"
).str.lower()

hierarchy_df["match_key"] = (
    hierarchy_df["level_5_name"]
    .str.replace("Powiat m. st. ", "", regex=False)
    .str.replace("Powiat m. ", "", regex=False)
    .str.replace("Powiat ", "", regex=False)
    + " ("
    + hierarchy_df["level_2_name"]
    + ")"
).str.lower()

# Ceased to exist in 2002
index_to_drop = hierarchy_df.query('match_key == "warszawski (mazowieckie)"').index[0]
hierarchy_df = hierarchy_df.drop(index_to_drop)

# Duplicate with Wałbrzych
index_to_drop = hierarchy_df.query(
    'match_key == "wałbrzych do 2002 (dolnośląskie)"'
).index[0]
hierarchy_df = hierarchy_df.drop(index_to_drop)

hierarchy_df["match_key"] = hierarchy_df["match_key"].replace(
    "wałbrzych od 2013 (dolnośląskie)", "wałbrzych (dolnośląskie)"
)

df = hierarchy_df.merge(teryt_df, on="match_key", validate="one_to_one")

# -------------------------------------------------------------------

export_df = df[
    [
        "nuts_3_code",
        "teryt_code",
        "nuts_3_name",
        "powiat_name",
        "powiat_name_extra",
        "voivodship_name",
        "voivodship_name_extra",
        "level_5_name",
        "level_4_name",
        "level_3_name",
        "level_2_name",
        "level_1_name",
    ]
]

# Export to CSV with quoted text
combined_path = "../../data/poland/intermediate_datasets/poland__region_id.csv"
export_df.to_csv(combined_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
print("Combined dataset saved.")
