import os
import pandas as pd
from glob import glob
import csv

# Define directory paths
intermediate_dir = os.path.join(
    os.path.dirname(__file__), "../../data/poland/intermediate_datasets"
)
harmonised_dir = os.path.join(os.path.dirname(__file__), "../../data/poland/harmonised_datasets")

file_pattern = os.path.join(intermediate_dir, "poland__parliament*.csv")
csv_files = glob(file_pattern)

if not csv_files:
    raise ValueError("No files found")

# Function to aggregate text columns
def smart_text_agg(series):
    unique_vals = series.dropna().unique()
    return unique_vals[0] if len(unique_vals) == 1 else ' and '.join(sorted(set(unique_vals)))

for file_path in sorted(csv_files):
    standard_name = os.path.basename(file_path)[: len("poland__parliament_2000")]
    output_path = os.path.join(harmonised_dir, f"{standard_name}.csv")

    election_df = pd.read_csv(file_path)

    # Separate columns
    group_col = "nuts_3_code"
    numeric_cols = election_df.select_dtypes(include="number").columns
    text_cols = election_df.select_dtypes(exclude="number").columns.drop(group_col)
    
    agg_dict = {col: "sum" for col in numeric_cols}
    agg_dict.update({col: smart_text_agg for col in text_cols})
    aggregated_df = election_df.groupby(group_col, dropna=False).agg(agg_dict).reset_index()

    aggregated_df.to_csv(output_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
