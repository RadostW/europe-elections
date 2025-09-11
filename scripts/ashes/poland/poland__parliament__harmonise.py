import os
import pandas as pd
from glob import glob
import csv
import yaml

# Define directory paths
intermediate_dir = os.path.join(
    os.path.dirname(__file__), "../../data/poland/intermediate_datasets"
)
base_dir = os.path.join(os.path.dirname(__file__), "../../data/poland/raw_datasets")

replacements_path = os.path.join(
    os.path.dirname(__file__), "poland__parliament__replacements.yaml"
)

with open(replacements_path, 'r') as file:
    config = yaml.safe_load(file)

print("Using config:")
print(config)

def validate_merge(df_left, df_right, key):
    keys_left, keys_right = set(df_left[key].unique()), set(df_right[key].unique())

    # Find missing keys
    missing_in_right = keys_left - keys_right
    missing_in_left = keys_right - keys_left

    if missing_in_right:
        print(f"Keys in df_left but missing in df_right: {missing_in_right}")
    if missing_in_left:
        print(f"Keys in df_right but missing in df_left: {missing_in_left}")

    # Check for duplicate keys
    duplicates_left = df_left[key].duplicated().any()
    duplicates_right = df_right[key].duplicated().any()

    if duplicates_left:
        print("Duplicate keys found in df_left.")
    if duplicates_right:
        print("Duplicate keys found in df_right.")

    return not (
        missing_in_right or missing_in_left or duplicates_left or duplicates_right
    )

def get_replacements(standard_name):    
    return config[standard_name]["candidates_replacements"], config[standard_name]["other_replacements"]

def get_delimiter(standard_name):
    return config[standard_name]["delimiter"]

def get_teryt_column(standard_name):
    return config[standard_name]["teryt_column"]

def standardize_teryt(df):
    max = df["teryt_code"].max()
    if 999 < max and max < 10_000:        
        df["teryt_code"] = "T_" + df["teryt_code"].astype(int).astype(str).str.zfill(4)
    elif 99999 < max and max < 1_000_000:
        df["teryt_code"] = "T_" + df["teryt_code"].astype(int).astype(str).str.zfill(6).str[:4]
    else:
        raise NotImplementedError

# Function to process and clean election data
def process_election_data(file_path, regions_df, output_path, standard_name):
    delimiter = get_delimiter(standard_name)
    election_df = pd.read_csv(file_path, delimiter=delimiter)

    election_df["teryt_code"] = election_df[get_teryt_column(standard_name)].copy()
    standardize_teryt(election_df)

    renamed_powiats = {
        "T_1431": "T_1465",  # warszawski -> m. Warszawa
        "T_0263": "T_0265",  # Wałbrzych -> Wałbrzych
    }
    election_df["teryt_code"].replace(renamed_powiats, inplace=True)


    candidates_replacements, other_replacements = get_replacements(standard_name)

    # Validate and merge with regions dataframe
    validate_merge(election_df, regions_df, "teryt_code")
    export_df = election_df.merge(regions_df, how="outer", on="teryt_code")

    # Rename columns and fill missing values
    export_df.rename(columns=candidates_replacements, inplace=True)
    export_df.rename(columns=other_replacements, inplace=True)

    # no data -> zero votes
    cols = list(candidates_replacements.values())
    export_df[cols] = export_df[cols].fillna(0.0)
    export_df[cols] = export_df[cols].astype(float)

    

    if "invalid_balots" not in export_df.columns:
        # best guess on number of invalid ballots
        export_df["valid_ballots"] = export_df[list(candidates_replacements.values())].sum(axis = 1)
        export_df["invalid_ballots"] = export_df["issued_ballots"] - export_df["valid_ballots"]
    
    export_df.fillna(-1, inplace=True) # no data -> invalid

    # Define the order of columns and export the cleaned data
    prefix_columns = [
        "nuts_3_code",
        "nuts_3_name",
        "powiat_name",
        "powiat_name_extra",
        "teryt_code",
        "eligible_voters",
        "issued_ballots",
        "invalid_ballots",
    ]    
    suffix_columns = [
        "voivodship_name",
        "voivodship_name_extra",
        "level_5_name",
        "level_4_name",
        "level_3_name",
        "level_2_name",
        "level_1_name",
    ]
    columns_to_export = (
        prefix_columns + sorted(list(candidates_replacements.values())) + suffix_columns
    )
    export_df = export_df[columns_to_export]

    export_df.to_csv(output_path, index=False, quoting=csv.QUOTE_NONNUMERIC)


# Main code execution
file_pattern = os.path.join(base_dir, "poland__parliament*.csv")
csv_files = glob(file_pattern)

regions_file = os.path.join(base_dir, "../intermediate_datasets/poland__region_id.csv")
regions_df = pd.read_csv(regions_file)

if not csv_files:
    raise ValueError("No files found")

for file_path in sorted(csv_files):
    print(f"Loading file: {os.path.basename(file_path)}")
    try:
        standard_name = os.path.basename(file_path)[: len("poland__parilament_2000")]
        output_path = os.path.join(intermediate_dir, f"{standard_name}.csv")

        process_election_data(file_path, regions_df, output_path, standard_name)

    except Exception as e:
        print(f"Failed processing {os.path.basename(file_path)}: {e}")
        raise e
