# Read README.md in ../data/italy to understand the data better

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

config_path = (
    here / "../data/italy/raw_datasets/metadata/replacement_rules_comunes.yaml"
)

files_to_parse = sorted(
    list((here / "../data/italy/raw_datasets/province").resolve().glob("*.csv"))
)

nuts_2024_path = here / "../data/italy/raw_datasets/metadata/nuts_2024_official.csv"
comune_to_nuts_2024_path = (
    here / "../data/italy/raw_datasets/metadata/Italy-LAU-2024-NUTS-2024.csv"
)

df_nuts_raw = pd.read_csv(
    nuts_2024_path,
)

df_comune_to_nuts_2024 = pd.read_csv(
    comune_to_nuts_2024_path,
)

variazioni_path = here / "../data/italy/raw_datasets/metadata/variazioni_amministrative.csv"
df_variazioni = pd.read_csv(
    variazioni_path,
)


def normalize_string(x):
    return re.sub(r"[^A-Za-z ]", "", (unidecode.unidecode(x)).lower())

df_nuts_raw["nuts_clean"] = [
    normalize_string(x) for x in df_nuts_raw["NUTS label"]
]

df_nuts = pd.merge(
    df_comune_to_nuts_2024, df_nuts_raw, left_on="NUTS 3 CODE", right_on="NUTS Code"
)

df_nuts["comune_clean"] = [
    normalize_string(x.strip()) for x in df_nuts["LAU NAME NATIONAL"]
]

with open(config_path.resolve(), "r", encoding="utf-8") as in_file:
    try:
        config = yaml.safe_load(in_file)
    except yaml.YAMLError as exc:
        print(exc)

for file_path in files_to_parse:
    print(f"Parsing file: {file_path.name}")

    pattern = r"^(\d{8})__"
    match = re.search(pattern, file_path.name)
    if match:
        date_str = match.group(1)
    else:
        raise ValueError(f"No date found in filename: {file_path}")

    # print(f"{date_str=}")
    if date_str in [
        "19990613",
        "20080413",
        "20090607",
        "20130224",
        "20140525",

        "19960421",
        "20010513",
        
        "20220925",
    ]:
        df = pd.read_csv(
            file_path,
            sep=";",
        )
    elif date_str in [
        "20040612",
        "20060409",
        "20190526",
        "20240609",
        "20180304",
    ]:
        df = pd.read_csv(
            file_path,
            sep=";",
            encoding="cp1252",
        )
    elif date_str in [
        
    ]:
        continue  # province data missing - fix pending
    else:
        raise ValueError(f"Unrecognised date {date_str}")
    
    if "vaosta" in str(file_path.name).lower():
            continue

    columns = df.columns
    
    print(df.iloc[0])

    for c in columns:
        is_target = False
        target_name = ''
        for key,targets in config["column_names"].items():
            if c in targets:
                is_target = True
                target_name = key
                df = df.rename(columns={c:target_name})
        
        print(f"{'+' if is_target else ' '} {c[:20].ljust(20) + ('...' if len(c) > 20 else '   ')} -> {target_name}")        

    print(df.iloc[0])

    df["comune_clean"] = [
        normalize_string(x) for x in df["comune"]
    ]

    nuts_comunes = set(df_nuts["comune_clean"])
    nuts_comunes_no_spaces = set(re.sub(r" ", "", c) for c in nuts_comunes)

    # TODO rewrite:
    # 1 - match only exact, and check province (if available)    
    # 2 - match only exact
    # 3 - snap to dominant value in fine grain
    # 4 - raport percentage of level 1,2,3 matches

    def process_row_greedy(row):

        this_comune = row["comune_clean"]
        this_comune = this_comune.replace("parte del comune di ","")

        match_type = "unknown"
        comments = []
        nuts3_region = ""
        nuts_lau_name = ""        

        if this_comune in nuts_comunes:
            possible_targets = df_nuts[df_nuts["comune_clean"] == this_comune]
            nuts_lau_name = this_comune

            if len(possible_targets) == 1:
                comments.append("(one found in reference)")

                match_type = 'exact'
                nuts3_region = possible_targets.iloc[0]["nuts_clean"]
            else:                
                comments.append("(multiple found in reference)")

                match_type = 'exact_multi'
                nuts3_region = possible_targets.iloc[0]["nuts_clean"]
        else:
            comments.append("(not found in reference)")
            
            match_type = "fail"
            
            if this_comune.replace(" ","") in nuts_comunes_no_spaces:
                c = [x for x in nuts_comunes if this_comune.replace(" ","") == x.replace(" ","")][0] 
                comments.append("(match without spaces)")
                match_type = "exact"
                possible_targets = df_nuts[df_nuts["comune_clean"] == c]
                nuts3_region = possible_targets.iloc[0]["nuts_clean"]
                nuts_lau_name = c

            for c in nuts_comunes:
                if this_comune in c:
                    comments.append("(match as substring)")                    
                    match_type = "heuristic_multi"
                    possible_targets = df_nuts[df_nuts["comune_clean"] == c]
                    nuts3_region = possible_targets.iloc[0]["nuts_clean"]
                    nuts_lau_name = c
            
        return {            
            "nuts3_region": nuts3_region,            
            "nuts_lau_name": nuts_lau_name,
            "match_type" : match_type,
            "comment": " ".join(comments)
        }
    
    df = df.head(20_000)

    df_nuts_matches = pd.DataFrame(df.apply(process_row_greedy, axis=1,result_type="expand"))
    df_with_nuts = pd.concat([df, df_nuts_matches], axis=1)

    def process_row_heuristic():
        # for row pick known properties, 
        # select most fine grained property by checking number of values,
        # check what regions are assigned to these values 
        # snap to dominant value

    df_with_nuts = 

    raise NotImplementedError   