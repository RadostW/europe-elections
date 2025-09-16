# Read README.md in ../data/germany to understand the data better

import pathlib
import pandas as pd
import json
import numpy as np

#
# Script configuration
#

here = pathlib.Path(__file__).resolve().parent

croswalks_file = here / "../data/germany/raw_datasets/metadata/germany__cty_crosswalks.csv"



wikipedia_file = (
    here
    / "../data/germany/raw_datasets/metadata/germany__wikipedia_nuts_names.csv"
)

lookup_file = (
    here
    / "../data/germany/raw_datasets/metadata/germany__Regionen_20DE_20NUTS-3_20KGS.csv"
)

#
# Processing
#

df_admin = pd.read_csv(croswalks_file)
df_admin = (
    df_admin.sort_values(["county_code", "year"])
            .drop_duplicates("county_code", keep="last")
)

df_wikipedia = pd.read_csv(wikipedia_file)

df_lookup_file = pd.read_csv(lookup_file)

df_merge_a = pd.merge(df_wikipedia,df_lookup_file,how="outer",left_on="Code.2",right_on="NUTS-3")
df_merge_b = pd.merge(df_merge_a,df_admin,how="outer",left_on="KGS",right_on="county_code")

## TODO: only use the codes which are necessary for the harmonised dataset