import tqdm
import itertools
import pandas as pd
import numpy as np
import glob
import re
import pathlib

# --- Helper function to extract year from column name ---
def extract_year(col_name):
    match = re.search(r'31\.12\.(\d{4})', col_name)
    if match:
        return int(match.group(1))
    return None

# --- Step 1: Load all Excel files and sheets into crosswalks ---
crosswalks_pop = {}  # population-proportional
crosswalks_area = {}  # area-proportional

here = pathlib.Path(__file__).resolve().parent
file_paths = [(
    here
    / "../data/germany/raw_datasets/metadata/ref-kreise-1990-2023.xlsx"
)]

for file in file_paths:
    print(file)
    xls = pd.ExcelFile(file)
    for sheet_name in xls.sheet_names:
        print(sheet_name)
        df = pd.read_excel(file, sheet_name=sheet_name)

        kreise_cols = [c for c in df.columns if c.startswith("Kreise") and extract_year(c) is not None]
        if len(kreise_cols) != 2:
            print(f"Skipping sheet {sheet_name} in {file}, unexpected number of 'Kreise' columns")
            continue

        years = [extract_year(c) for c in kreise_cols]
        src_col, tgt_col = (kreise_cols[0], kreise_cols[1]) if years[0] < years[1] else (kreise_cols[1], kreise_cols[0])
        src_year = min(years)
        tgt_year = max(years)

        # if(src_year) > 1995: # for debugging
        #     continue

        # Names
        src_name_col = [c for c in df.columns if f"Kreisname {src_year}" in c][0]
        tgt_name_col = [c for c in df.columns if f"Kreisname {tgt_year}" in c][0]

        # Population proportion
        pop_col = [c for c in df.columns if "bevölkerungs" in c.lower()]
        if pop_col:
            prop_pop = pop_col[0]
        else:
            prop_pop = None

        # Area proportion
        area_col = [c for c in df.columns if "flächen" in c.lower()]
        if area_col:
            prop_area = area_col[0]
        else:
            prop_area = None

        # --- Population-proportional DataFrame ---
        cols_pop = [src_col, src_name_col, tgt_col, tgt_name_col, prop_pop] if prop_pop else [src_col, src_name_col, tgt_col, tgt_name_col]
        df_pop = df[cols_pop].rename(columns={
            src_col: "code_from",
            src_name_col: "name_from",
            tgt_col: "code_to",
            tgt_name_col: "name_to",
            prop_pop: "proportion" if prop_pop else "proportion"
        })
        df_pop['proportion'] = df_pop['proportion'].fillna(1.0)

        # --- Normalize population proportions per source code ---
        for code in df_pop['code_from'].unique():
            mask = df_pop['code_from'] == code
            total_prop = df_pop.loc[mask, 'proportion'].sum()
            if not np.isclose(total_prop, 1.0):
                print(f"Warning: population proportions for code {code} in year {src_year} sum to {total_prop:.3f}, normalizing")
                df_pop.loc[mask, 'proportion'] /= total_prop

        crosswalks_pop[src_year] = df_pop

        # --- Area-proportional DataFrame ---
        cols_area = [src_col, src_name_col, tgt_col, tgt_name_col, prop_area] if prop_area else [src_col, src_name_col, tgt_col, tgt_name_col]
        df_area = df[cols_area].rename(columns={
            src_col: "code_from",
            src_name_col: "name_from",
            tgt_col: "code_to",
            tgt_name_col: "name_to",
            prop_area: "proportion" if prop_area else "proportion"
        })
        df_area['proportion'] = df_area['proportion'].fillna(1.0)

        # --- Normalize area proportions per source code ---
        for code in df_area['code_from'].unique():
            mask = df_area['code_from'] == code
            total_prop = df_area.loc[mask, 'proportion'].sum()
            if not np.isclose(total_prop, 1.0):
                print(f"Warning: area proportions for code {code} in year {src_year} sum to {total_prop:.3f}, normalizing")
                df_area.loc[mask, 'proportion'] /= total_prop

        crosswalks_area[src_year] = df_area

# --- Step 2: Sort years ---
sorted_years = sorted(crosswalks_pop.keys())  # same years for area
latest_year = max(sorted_years)

# --- Step 3: Extract all unique year-code pairs ---
all_codes = []
for src_year, df in crosswalks_pop.items():
    for _, row in df.iterrows():
        all_codes.append((row['code_from'], src_year, row['name_from']))
all_codes = list({(c, y, n) for c, y, n in all_codes})  # remove duplicates

# --- Step 4: Cascading mapping function for splits ---
def map_to_latest_with_splits(crosswalks, code_start, year_start, prop_start=1.0):
    active = [(code_start, [], prop_start)]
    for year in sorted_years:
        if year < year_start:
            continue
        next_active = []
        df = crosswalks[year]
        for code, name_chain, prop in active:
            matches = df[df['code_from'] == code]
            if matches.empty:
                next_active.append((code, name_chain, prop))
            else:
                for _, row in matches.iterrows():
                    new_code = row['code_to']
                    new_name_chain = name_chain + [(row['name_from'], row['name_to'])]
                    new_prop = prop * row['proportion']
                    next_active.append((new_code, new_name_chain, new_prop))
        active = next_active
    return active

# --- Step 5: Apply mapping for population and area ---
results = []
for code, src_year, name_from in tqdm.tqdm(all_codes):
    # Population
    # print(f"mapping: {src_year}-{name_from}")
    mapped_pop = map_to_latest_with_splits(crosswalks_pop, code, src_year)    
    
    prop_lst = [prop for final_code, name_chain, prop in mapped_pop]
    total_prop = sum(prop_lst)
    if not np.isclose(total_prop, 1.0):
        print("probability leak")

    #if len(prop_lst) > 1:
    #    print(mapped_pop)

    for final_code, name_chain, prop in mapped_pop:
        if prop != 1.0:
            print(f"{prop:.2f}: {name_from}->{name_chain[-1]}")            
        
        results.append({
            "code_start": code,
            "year_start": src_year,                
            "name_start": name_from,

            "code_latest": final_code,
            "name_latest": name_chain[-1][-1],

            "name_chain": " -> ".join(str(k) for k, _ in itertools.groupby([new for _, new in name_chain])),
            "proportion_population": prop,
            "proportion_area": None
        })

    # Area
    mapped_area = map_to_latest_with_splits(crosswalks_area, code, src_year)
    for idx, (final_code, name_chain, prop) in enumerate(mapped_area):    
        results.append({
            "code_start": code,
            "year_start": src_year,                
            "name_start": name_from,

            "code_latest": final_code,
            "name_latest": name_chain[-1][-1],

            "name_chain": " -> ".join(str(k) for k, _ in itertools.groupby([new for _, new in name_chain])),
            "proportion_population": None,
            "proportion_area": prop
        })    

# --- Step 6: Save results ---
df_results = pd.DataFrame(results)

df_results = (
    df_results
    .groupby(
        ["code_start", "year_start", "name_start", "code_latest", "name_latest"],
        as_index=False
    )
    .agg({
        "proportion_population": "sum",
        "proportion_area": "sum",
        "name_chain": lambda x: " and ".join(x.dropna().unique())
    })
    .sort_values(["year_start", "code_start", "code_latest"])
    .reset_index(drop=True)
)

df_results["code_start"] = "A_" + df_results["code_start"].astype(int).astype(str).str.zfill(8)
df_results["code_latest"] = "A_" + df_results["code_latest"].astype(int).astype(str).str.zfill(8)

output_path = here / (
                f"../data/germany/harmonised/kreisen/germany__crosswalks.csv"
            )
df_results.to_csv(output_path,index=False)

# df_results.to_excel("cascading_crosswalk_population_area.xlsx", index=False)
# print("Cascading crosswalk (population + area) saved to cascading_crosswalk_population_area.xlsx")
