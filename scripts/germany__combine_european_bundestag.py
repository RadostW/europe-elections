# Read README.md in ../data/germany to understand the data better

import pathlib
import pandas as pd
import numpy as np
import re

here = pathlib.Path(__file__).resolve().parent

european_file = (
    (here / "../data/germany/harmonised/kreisen/germany__european_long.csv")
)

bundestag_file = (
    (here / "../data/germany/harmonised/kreisen/germany__bundestag_long.csv")
)

df_bundestag = pd.read_csv(bundestag_file, index_col=0)
df_european  = pd.read_csv(european_file, index_col=0)

# --- Combine into a single DataFrame
df_all = pd.concat([df_bundestag, df_european], ignore_index=True)

df_all = df_all.sort_values('election_date', kind='stable').reset_index(drop=True)

output_path = (
    here
    / "../data/germany/harmonised/kreisen/germany__long.csv"
)

df_all.to_csv(output_path)