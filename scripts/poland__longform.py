import pathlib
import pandas as pd
import re

here = pathlib.Path(__file__).resolve().parent

files_to_parse = (
    (here / "../data/poland/harmonised/powiaty").resolve().glob("poland__*.csv")
)

# Regex to capture election name and date
pattern = re.compile(r"poland__(.+?)__(\d{4}_\d{2}_\d{2})\.csv")

# Columns that are always present and not parties
fixed_columns = ["teryt_code"]

# Load harmonised region metadata
metadata_file = here / "../data/poland/harmonised/powiaty/poland__region_data.csv"
region_df = pd.read_csv(metadata_file, index_col=0)
# Assume region_df has columns: 'teryt', 'pow_name'
region_mapping = region_df.set_index("teryt")["pow_name"].to_dict()

manual_labels = {
    "T_1499": "abroad",
    "T_2299": "ships",
    "T_2298": "ships",
    "T_3299": "ships",
    "T_1498": "ships",
}

# Insert but throw if already present
for k, v in manual_labels.items():
    if k in region_mapping:
        raise ValueError(
            f"Attempted to override existing mapping for {k}: "
            f"{region_mapping[k]} -> {v}"
        )
    region_mapping[k] = v


long_dfs = []

for file_path in sorted(files_to_parse):
    m = pattern.search(file_path.name)
    if not m:
        continue

    election_name = m.group(1).replace("__", "_")
    date_str = m.group(2)
    print(f"Election: {election_name}, Date: {date_str}")

    df = pd.read_csv(file_path, index_col=0)

    # Melt all columns except teryt_code
    melt_cols = [c for c in df.columns if c != "teryt_code"]
    df_long = df.melt(
        id_vars=["teryt_code"],
        value_vars=melt_cols,
        var_name="name",
        value_name="votes",
    )

    # Assign type based on column name
    def assign_type(col_name):
        if col_name == "eligible_voters":
            return 0
        elif col_name == "issued_ballots":
            return 1
        else:
            return 2  # party/candidate votes

    df_long["type"] = df_long["name"].apply(assign_type)

    # Add metadata
    df_long["election_date"] = date_str
    df_long["election_type"] = election_name
    df_long["harmonised_code"] = df_long["teryt_code"]
    df_long["harmonised_code"] = df_long["harmonised_code"].replace(
        {
            "T_1431": "T_1465", # old code for warsaw -> new
            "T_0263": "T_0265", # old code for walbrzych -> new
        }
    )

    # Map harmonised names and warn about missing codes
    df_long["harmonised_name"] = df_long["harmonised_code"].map(region_mapping)
    missing_codes = df_long[df_long["harmonised_name"].isna()]["teryt_code"].unique()
    if len(missing_codes) > 0:
        print(f"Warning: Missing harmonised names for codes: {missing_codes}")

    # Reorder columns
    df_long = df_long[
        [
            "election_date",
            "election_type",
            "harmonised_code",
            "harmonised_name",
            "type",
            "name",
            "votes",
        ]
    ]

    long_dfs.append(df_long)

# Concatenate all files into one long DataFrame
final_long_df = pd.concat(long_dfs, ignore_index=True)

# Sort for convenience
final_long_df = final_long_df.sort_values(
    ["election_date", "harmonised_code", "type"], kind="stable"
).reset_index(drop=True)

output_path = (
    here
    / "../data/poland/harmonised/powiaty/poland__long.csv"
)
final_long_df.to_csv(output_path)