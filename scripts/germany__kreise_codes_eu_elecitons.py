# Read README.md in ../data/germany to understand the data better

import yaml
import itertools
import pathlib
import pandas as pd
import numpy as np
import re
import traceback

here = pathlib.Path(__file__).resolve().parent

files_to_parse = (
    (here / "../data/germany/harmonised/kreisen").resolve().glob("germany__european*.csv")
)

kreise_codes = pd.DataFrame()

for file_path in sorted(files_to_parse):
    print(f"Parsing file: {file_path.name}")
    df = pd.read_csv(file_path)

    pattern = r"(\d{4}_\d{2}_\d{2})"
    match = re.search(pattern, file_path.name)
    if match:
        date_str = match.group(1)
    else:
        raise ValueError(f"No date found in filename: {file_path}")
    
    if len(kreise_codes) == 0:
        kreise_codes = df[["teryt_code"]].copy()
        kreise_codes[date_str] = 1
    else:        
        df[date_str] = 1
        kreise_codes = pd.merge(df[["teryt_code",date_str]],kreise_codes,on="teryt_code",how="outer")        


kreise_codes = kreise_codes.fillna(0)
indicator_columns = [x for x in  kreise_codes.columns if x !=  'teryt_code']
for c in indicator_columns:
    kreise_codes[c] = kreise_codes[c].astype(int)

kreise_codes.to_csv('kreise_codes_debug.csv')