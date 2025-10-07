import pandas as pd
import pathlib
from tqdm import tqdm

tqdm.pandas()

# ---------------------------
# Paths
# ---------------------------
here = pathlib.Path(__file__).resolve().parent
election_file = here / "../data/france/raw_datasets/departament/france__raw_big.csv"
output_file = election_file.parent / "france__departament.csv"

# ---------------------------
# Chunk and data config
# ---------------------------
chunksize = 200_000
max_chunks = 1000  # for debugging

# Columns to sum
sum_cols = ["Voix"]

# Candidate/List columns (replace NaN with 'missing')
group_cols = [
    "id_election",
    "Code du département",
    "Libellé Abrégé Liste",
    "Libellé Etendu Liste",
    "Nom Tête de Liste",
    "Nom",
    "Prénom",
    "Nuance",
    "Binôme",
    "Liste",
]

# Metadata columns to check consistency
meta_cols = ["Sexe"]

# Explicit dtypes
dtype_dict = {
    "id_election": str,
    "id_brut_miom": str,
    "Code du département": str,
    "Code de la commune": str,
    "Code du b.vote": str,
    "N°Panneau": str,
    "Libellé Abrégé Liste": str,
    "Libellé Etendu Liste": str,
    "Nom Tête de Liste": str,
    "Sexe": str,
    "Nom": str,
    "Prénom": str,
    "Nuance": str,
    "Binôme": str,
    "Liste": str,
    "Voix": "Int64",
    "% Voix/Ins": float,
    "% Voix/Exp": float,
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

reader = pd.read_csv(election_file, sep=";", chunksize=chunksize, dtype=dtype_dict)
for i, chunk in enumerate(tqdm(reader, desc="Processing chunks", total=136)):
    if i >= max_chunks:  # limit chunks for debugging
        break

    # Drop municipal elections
    chunk = chunk[~chunk["id_election"].str.contains("muni")].copy()

    if chunk.empty:
        continue

    # Replace NaN with 'missing' in group columns
    chunk.loc[:, group_cols] = chunk.loc[:, group_cols].fillna("missing")

    agg_dict = {col: "sum" for col in sum_cols}
    agg_dict.update({col: constant_or_mixed for col in meta_cols})

    grouped = chunk.groupby(group_cols, as_index=False).agg(agg_dict)

    # Add row_count per group
    grouped["row_count"] = chunk.groupby(group_cols).size().values

    partial_results.append(grouped)

# ---------------------------
# Combine partial results
# ---------------------------
print("fusing")

if partial_results:
    combined = pd.concat(partial_results, ignore_index=True)

    final = combined.groupby(group_cols, as_index=False).agg(
        {
            **{col: "sum" for col in sum_cols + ["row_count"]},
            **{col: constant_or_mixed for col in meta_cols},
        }
    )

    column_rename = {
        "id_election": "election_id",
        "Code du département": "department_code",
        "Libellé Abrégé Liste": "list_label_short",
        "Libellé Etendu Liste": "list_label_long",
        "Nom Tête de Liste": "list_head_name",
        "Nom": "last_name",
        "Prénom": "first_name",
        "Nuance": "political_orientation",
        "Binôme": "ticket_pair",
        "Liste": "list_name",
        "Voix": "votes",
        "row_count": "row_count",
        "Sexe": "gender",
    }

    final = final.rename(columns=column_rename)
    final.to_csv(output_file, sep=";", index=False)

    # ---------------------------
    # Save result
    # ---------------------------
    final.to_csv(output_file, index=False)
    print(f"Debug digest saved to {output_file}")
    print(final.head())
else:
    print(f"No non-municipal election rows found in the first {max_chunks} chunks.")
