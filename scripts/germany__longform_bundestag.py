# Read README.md in ../data/germany to understand the data better

import pathlib
import pandas as pd
import numpy as np
import re

here = pathlib.Path(__file__).resolve().parent

files_to_parse = (
    (here / "../data/germany/harmonised/kreisen").resolve().glob("germany__bundestag*.csv")
)

crosswalk_file = (
    (here / "../data/germany/harmonised/kreisen/germany__crosswalks.csv")
)

df_cross = pd.read_csv(crosswalk_file)
if (df_cross["code_start"].str.endswith("000") == False).any():
    raise ValueError("Unable to simplify source codes")
if (df_cross["code_latest"].str.endswith("000") == False).any():
    raise ValueError("Unable to simplify destination codes")

# Remove trailing "000"
df_cross["code_start"] = df_cross["code_start"].str[:-3]
df_cross["code_latest"] = df_cross["code_latest"].str[:-3]

all_dfs = []

for file_path in sorted(files_to_parse):
    year = re.search(r"__(\d{4})_", file_path.name).group(1)
    date = re.search(r"__(\d{4}_\d{2}_\d{2})", file_path.name).group(1)
    crosswalk_year = 2021
    # min([int(year),2022]) # no croswalks available for 2022 onwards    

    print(f"Parsing file: {file_path.name}, year: {crosswalk_year}")


    df = pd.read_csv(file_path)

    # --- Step 1: ensure teryt_code strings
    df['teryt_code'] = df['teryt_code'].astype(str)

    # --- Split crosswalk into two candidate sets
    cw_prev = df_cross.query(f"year_start == {int(crosswalk_year)-1}")[['code_start', 'code_latest', 'proportion_population', 'name_latest']]
    cw_curr = df_cross.query(f"year_start == {int(crosswalk_year)}")[['code_start', 'code_latest', 'proportion_population', 'name_latest']]

    # --- Match in two stages
    codes_needed = set(df['teryt_code'])

    # First: take those present in year-1
    codes_prev = codes_needed & set(cw_prev['code_start'])
    cw_used = cw_prev[cw_prev['code_start'].isin(codes_prev)]

    # Remaining: try from year
    codes_remaining = codes_needed - codes_prev
    codes_curr = codes_remaining & set(cw_curr['code_start'])
    cw_used = pd.concat([cw_used, cw_curr[cw_curr['code_start'].isin(codes_curr)]], ignore_index=True)

    # Final unmatched check
    codes_unmatched = codes_remaining - codes_curr
    if codes_unmatched:
        raise ValueError(
            f"Missing codes in crosswalk for year {crosswalk_year} (showing up to 20): "
            f"{sorted(list(codes_unmatched))[:20]}"
        )

    # --- Step 2: validate proportions
    prop_sums = cw_used.groupby('code_start')['proportion_population'].sum()

    bad = prop_sums[~np.isclose(prop_sums, 1.0, atol=0.01)]

    if not bad.empty:
        raise ValueError(
            "proportion_population for some code_start do not sum to 1 (±0.01 tolerance): "
            f"{bad.head(20).to_dict()}"
        )

    cw = cw_used
        
    # --- Step 2: expand input rows to one row per matching code_latest (one-to-many)
    
    df_expanded = df.merge(
        cw,
        left_on='teryt_code',
        right_on='code_start',
        how='left',
        validate='one_to_many',  # left keys (teryt_code) expected to map to 1..n cw rows
    )    

    if df_expanded['code_latest'].isna().any():
        raise ValueError("Some rows did not match any crosswalk entry after merge")

    # --- Identify which columns to scale (party votes + optionally eligible/issued)
    metadata = {
        'Unnamed: 0', 'teryt_code', 'original_teryt_code',
        'code_start', 'code_latest', 'proportion_population', 'name_latest'
    }
    # treat eligible_voters and issued_ballots as scalars that should be split
    # party columns are everything in the original df except metadata
    party_cols = [c for c in df.columns if c not in metadata]
    scale_cols = [c for c in party_cols if c in df_expanded.columns]
    for c in ('eligible_voters', 'issued_ballots'):
        if c in df_expanded.columns and c not in scale_cols:
            scale_cols.append(c)

    # --- Coerce numeric (robust) and scale by proportion_population
    df_expanded[scale_cols] = df_expanded[scale_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    df_expanded['proportion_population'] = pd.to_numeric(df_expanded['proportion_population'], errors='coerce').fillna(0)

    for col in scale_cols:
        df_expanded[col] = df_expanded[col] * df_expanded['proportion_population']
    

    # --- Aggregate to code_latest
    agg_dict = {c: 'sum' for c in scale_cols}
    df_harmonised = df_expanded.groupby(['code_latest', 'name_latest'], as_index=False).agg(agg_dict)        

    # --- Rename columns
    df_harmonised = df_harmonised.rename(columns={
        'code_latest': 'harmonised_code',
        'name_latest': 'harmonised_name'
    })

    # --- Identify column types
    eligible_voter_cols = ['eligible_voters']  # replace with your actual column names
    issued_ballot_cols = ['issued_ballots']    # replace with your actual column names
    party_cols = [c for c in df_harmonised.columns 
                if c not in ['harmonised_code', 'harmonised_name'] + eligible_voter_cols + issued_ballot_cols]

    # --- Reorder party_cols by total votes descending
    party_cols_sorted = df_harmonised[party_cols].sum().sort_values(ascending=False).index.tolist()

    # --- Melt all at once, using the sorted party columns
    df_long = df_harmonised.melt(
        id_vars=['harmonised_code', 'harmonised_name'],
        value_vars=eligible_voter_cols + issued_ballot_cols + party_cols_sorted,
        var_name='name',
        value_name='votes'
    )

    # --- Map type
    type_map = {col: 0 for col in eligible_voter_cols}
    type_map.update({col: 1 for col in issued_ballot_cols})
    type_map.update({col: 2 for col in party_cols_sorted})

    df_long['type'] = df_long['name'].map(type_map)

    # --- Reorder columns
    df_long = df_long[['harmonised_code', 'harmonised_name', 'type', 'name', 'votes']]

    # --- Sort by code and type (eligible_voters, issued_ballots, then parties in total votes order)
    df_long = df_long.sort_values(
        ['harmonised_code', 'type'],
        kind='stable'  # keep the original order within each type
    ).reset_index(drop=True)

    # --- Add election metadata columns (replace with your actual values or columns)
    df_long['election_date'] = date
    df_long['election_type'] = 'bundestag'  

    # --- Move them to the leftmost positions
    df_long = df_long[['election_date', 'election_type', 
                    'harmonised_code', 'harmonised_name', 
                    'type', 'name', 'votes']]

    all_dfs.append(df_long.copy())

output_path = (
    here
    / "../data/germany/harmonised/kreisen/germany__bundestag_long.csv"
)

df_all = pd.concat(all_dfs, ignore_index=True)
df_all.to_csv(output_path)