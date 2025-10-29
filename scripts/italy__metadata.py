# Read README.md in ../data/italy to understand the data better

import pathlib
import pandas as pd
import numpy as np

here = pathlib.Path(__file__).resolve().parent

nuts_2024_path = here / "../data/italy/raw_datasets/metadata/nuts2024_all_levels.csv"

import pandas as pd

# Load and rename columns
df = pd.read_csv(nuts_2024_path)
df = df.rename(
    columns={
        "Country code": "country_code",
        "NUTS Code": "nuts_code",
        "NUTS label": "nuts_label",
        "NUTS level": "nuts_level",
    }
)

# Filter Italian NUTS levels
df_nuts1 = df.query("country_code == 'IT' and nuts_level == 1")
df_nuts2 = df.query("country_code == 'IT' and nuts_level == 2")
df_nuts3 = df.query("country_code == 'IT' and nuts_level == 3")

# Prepare NUTS3 with parent references
df_nuts3 = df_nuts3.rename(columns={"nuts_code": "nuts3_code"})
df_nuts3["nuts2_code"] = df_nuts3["nuts3_code"].str[:4]
df_nuts3["nuts1_code"] = df_nuts3["nuts3_code"].str[:3]

# Merge with NUTS2 and NUTS1 labels
df_merged = (
    df_nuts3
    .merge(df_nuts2[["nuts_code", "nuts_label"]], left_on="nuts2_code", right_on="nuts_code", how="left", suffixes=("", "_nuts2"))
    .merge(df_nuts1[["nuts_code", "nuts_label"]], left_on="nuts1_code", right_on="nuts_code", how="left", suffixes=("", "_nuts1"))
)

# Keep only the relevant columns
df_merged = df_merged[
    [
        "nuts3_code",
        "nuts_label",           # NUTS3 label
        "nuts2_code",
        "nuts_label_nuts2",     # NUTS2 label
        "nuts1_code",
        "nuts_label_nuts1"      # NUTS1 label
    ]
].rename(
    columns={
        "nuts_label": "nuts3_label",
        "nuts_label_nuts2": "nuts2_label",
        "nuts_label_nuts1": "nuts1_label"
    }
)

df_merged = df_merged.sort_values(by=["nuts1_code", "nuts2_code", "nuts3_code"]).reset_index(drop=True)

output_path = here / (
            f"../data/italy/harmonised/province/italy_metadata.csv"
        )
df_merged.to_csv(output_path)