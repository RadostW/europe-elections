import pandas as pd
import pathlib
from tqdm import tqdm

tqdm.pandas()

# ---------------------------
# Paths
# ---------------------------
here = pathlib.Path(__file__).resolve().parent
election_file = here / "../data/france/raw_datasets/departament/france__eligible_voters.csv"
output_file = election_file.parent / "france__departament_eligible.csv"

# ---------------------------
# Chunk config
# ---------------------------
chunksize = 200_000
max_chunks = 100_000  # for debugging

# Columns to sum
sum_cols = ["Inscrits", "Abstentions", "Votants", "Blancs", "Nuls", "Exprimés"]

# Group by department
group_cols = ["id_election", "Code du département", "Libellé du département"]

# Explicit dtypes
dtype_dict = {
    "id_election": str,
    "id_brut_miom": str,
    "Code du département": str,
    "Libellé du département": str,
    "Code de la commune": str,
    "Libellé de la commune": str,
    "Code du b.vote": str,
    "Inscrits": "Int64",
    "Abstentions": "Int64",
    "Votants": "Int64",
    "Blancs": "Int64",
    "Nuls": "Int64",
    "Exprimés": "Int64",
    "Code de la circonscription": str,
    "Libellé de la circonscription": str,
    "Code du canton": str,
    "Libellé du canton": str,
}

# ---------------------------
# Helper function
# ---------------------------
def constant_or_mixed(series):
    unique_vals = series.dropna().unique()
    if len(unique_vals) == 1:
        return unique_vals[0]
    elif len(unique_vals) == 0:
        return None
    else:
        return "MIXED"

# ---------------------------
# Process chunks
# ---------------------------
partial_results = []
meta_cols = False

reader = pd.read_csv(election_file, sep=";", chunksize=chunksize, dtype=dtype_dict)
for i, chunk in enumerate(tqdm(reader, desc="Processing chunks")):

    # -----------------------
    # Debug: chunk info
    # -----------------------
    print(f"\nChunk {i}: shape = {chunk.shape}")
    print("Columns before stripping:", chunk.columns.tolist())

    # Fix whitespace in column names
    chunk.columns = chunk.columns.str.strip()
    print("Columns after stripping:", chunk.columns.tolist())

    chunk["Libellé du département"] = chunk["Libellé du département"].fillna("missing")

    if not meta_cols:
        meta_cols = [col for col in chunk.columns if (col not in (sum_cols + group_cols))]
        print("Meta columns detected:", meta_cols)

    if i >= max_chunks:
        break

    if chunk.empty:
        print("Chunk is empty, skipping.")
        continue

    # -----------------------
    # Aggregation
    # -----------------------
    agg_dict = {col: "sum" for col in sum_cols}
    agg_dict.update({col: constant_or_mixed for col in meta_cols})

    grouped = chunk.groupby(group_cols, as_index=False).agg(agg_dict)

    # -----------------------
    # Safe row_count
    # -----------------------
    row_counts = chunk.groupby(group_cols).size().reset_index(name="row_count")
    grouped = grouped.merge(row_counts, on=group_cols, how="left")

    # -----------------------
    # Debug: check grouped
    # -----------------------
    print(f"Grouped shape: {grouped.shape}")
    if grouped.empty:
        print("Grouped dataframe is empty! Here is the chunk:")
        print(chunk.head())

    partial_results.append(grouped)

# ---------------------------
# Combine partial results
# ---------------------------
print("\nFusing partial results...")

if partial_results:
    combined = pd.concat(partial_results, ignore_index=True)
    print("Combined shape:", combined.shape)

    # Final aggregation
    final = combined.groupby(group_cols, as_index=False).agg(
        {
            **{col: "sum" for col in sum_cols + ["row_count"]},
            **{col: constant_or_mixed for col in meta_cols},
        }
    )

    # Rename columns
    column_rename = {
        "id_election": "election_id",
        "Code du département": "department_code",
        "Libellé du département": "department_name",
        "Inscrits": "eligible_voters",
        "Abstentions": "abstentions",
        "Votants": "voters",
        "Blancs": "blank_votes",
        "Nuls": "null_votes",
        "Exprimés": "valid_votes",
    }
    final = final.rename(columns=column_rename)

    final.to_csv(output_file, sep=",", index=False)
    print(f"Aggregated eligible voters saved to {output_file}")
    print(final.head())
else:
    print(f"No data found in the first {max_chunks} chunks.")
