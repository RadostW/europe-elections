import pandas as pd
import numpy as np
import pathlib
import unicodedata
import re

# ---------------------------
# Paths
# ---------------------------
here = pathlib.Path(__file__).resolve().parent
metadata_dir = here / "../data/france/raw_datasets/metadata/"
elections_file = here / "../data/france/harmonised/departament/france__long.csv"

df1 = pd.read_csv(metadata_dir / "nuts1.csv")
df2 = pd.read_csv(metadata_dir / "nuts2.csv")
df3 = pd.read_csv(metadata_dir / "nuts3.csv")
df_elections = pd.read_csv(elections_file, index_col=0)

# ---------------------------
# Combine NUTS hierarchically
# ---------------------------
df2["nuts1_code"] = df2["nuts2_code"].str[:3]  # NUTS1 parent code
df3["nuts2_code"] = df3["nuts3_code"].str[:4]  # NUTS2 parent code

df_merged = df3.merge(df2, on="nuts2_code", how="left").merge(
    df1, on="nuts1_code", how="left"
)

# ---------------------------
# Prepare unique election and NUTS names (including NUTS2/1)
# ---------------------------
df_election_names = (
    df_elections[["harmonised_code", "harmonised_name"]].drop_duplicates().copy()
)
df_nuts_names = (
    df_merged[
        [
            "nuts3_code",
            "nuts3_name",
            "nuts2_code",
            "nuts2_name",
            "nuts1_code",
            "nuts1_name",
        ]
    ]
    .drop_duplicates()
    .copy()
)

# ---------------------------
# Manual overrides
# ---------------------------
manual_matches = {
    "M_2A": "Corse-du-Sud",
    "M_971": "Guadeloupe et Saint Martin",
    "M_973": "French Guiana",
    "M_ZA": "Guadeloupe et Saint Martin",
    "M_ZC": "French Guiana",
    "M_ZX": "Guadeloupe et Saint Martin",
    "M_977": "Guadeloupe et Saint Martin",
}

# Copy harmonised_name → harmonised_name_fixed
df_election_names["harmonised_name_fixed"] = df_election_names.apply(
    lambda row: manual_matches.get(row["harmonised_code"], row["harmonised_name"]),
    axis=1,
)


# ---------------------------
# Normalize function
# ---------------------------
def normalize_name(name):
    if pd.isna(name):
        return None
    name_ascii = (
        unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    )
    name_ascii = name_ascii.lower()
    return re.sub(r"[^a-z0-9]", "", name_ascii)


df_election_names["norm_name"] = df_election_names["harmonised_name_fixed"].apply(
    normalize_name
)
df_nuts_names["norm_name"] = df_nuts_names["nuts3_name"].apply(normalize_name)

# ---------------------------
# Merge with outer join, keeping one row per harmonised_code
# ---------------------------
df_all_matches = df_election_names.merge(df_nuts_names, on="norm_name", how="outer")

df_all_matches["nuts"] = df_all_matches["nuts3_code"]

def split_nuts(nuts_code, start, end):
    if pd.isna(nuts_code):
        return np.nan
    return str(nuts_code)[start:end]

df_all_matches["nuts_0"] = df_all_matches["nuts"].apply(lambda x: split_nuts(x, 0, 2))
df_all_matches["nuts_1"] = df_all_matches["nuts"].apply(lambda x: split_nuts(x, 2, 3))
df_all_matches["nuts_2"] = df_all_matches["nuts"].apply(lambda x: split_nuts(x, 3, 4))
df_all_matches["nuts_3"] = df_all_matches["nuts"].apply(lambda x: split_nuts(x, 4, 5))


# Reorder columns for clarity
df_all_matches = df_all_matches[
    [
        "harmonised_code",
        "nuts", # nuts3 code
        "nuts_0",
        "nuts_1",
        "nuts_2",
        "nuts_3",        
        "harmonised_name",
        # "harmonised_name_fixed",        
        "nuts3_name",        
        "nuts2_name",        
        "nuts1_name",
    ]
]

df_all_matches = df_all_matches.sort_values(
    by=["nuts"],
    ascending=[True],
).reset_index(drop=True)

# ---------------------------
# Export
# ---------------------------
output_file = here / "../data/france/harmonised/departament/france__region_data.csv"
df_all_matches.to_csv(output_file)