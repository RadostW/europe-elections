import pandas as pd
import pathlib
import yaml

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------
here = pathlib.Path(__file__).resolve().parent

election_file = here / "../data/france/raw_datasets/departament/france__departament.csv"
output_file = election_file.parent / "france__long.csv"

config_path = here / "../data/france/raw_datasets/metadata/replacement_rules.yaml"

# ---------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------
print(f"Loading data from {election_file}")
df = pd.read_csv(election_file, low_memory=False)

with open(config_path.resolve(), "r", encoding="utf-8") as in_file:
    try:
        config = yaml.safe_load(in_file)
    except yaml.YAMLError as exc:
        print(exc)
        raise

# ---------------------------------------------------------------------
# Identify election types (example: extract from election_id)
# ---------------------------------------------------------------------
df["election_type"] = df["election_id"].str.extract(r"_(\D+)_", expand=False)
df["election_year"] = df["election_id"].str.extract(r"(\d{4})", expand=False)
df["round_string"] = df["election_id"].str.extract(r"_(t\d+)$", expand=False)

# ---------------------------------------------------------------------
# Prepare accumulator for processed data
# ---------------------------------------------------------------------
processed_chunks = []

# ---------------------------------------------------------------------
# Loop over election types
# ---------------------------------------------------------------------
for (election_type_short, election_year), subset in df.groupby(["election_type", "election_year"]):
    print(f"Processing election type: {election_type_short} ({len(subset)} rows)")

    # Example: handle only presidential elections
    if election_type_short == "pres":
        # Get first election_id in this subset (assuming consistent per election)
        election_id = subset["election_id"].iloc[0]
        round_string = subset["round_string"].iloc[0]

        # Lookup date from config
        election_date = config["election_id_to_date"].get(election_id, "unknown_date")

        # Determine full election type (add suffix for round)
        election_type = "president" + "_" + ("a" if round_string == "t1" else "b")

        def get_department_name(code):
            return config["department_code_to_name"][code]            

        harmonised = pd.DataFrame({
            "election_date": election_date,
            "election_type": election_type,
            "harmonised_code": "M_" + subset["department_code"].astype(str),
            "harmonised_name": ("M_"+subset["department_code"]).apply(get_department_name),
            "type": 2,  # 2 = votes for candidates
            "name": subset["last_name"].fillna("").str.title().str.replace(" ", "", regex=False),
            "votes": subset["votes"]
        })

        processed_chunks.append(harmonised)

    else:
        continue

# ---------------------------------------------------------------------
# Combine and save
# ---------------------------------------------------------------------
if processed_chunks:
    output_df = pd.concat(processed_chunks, ignore_index=True)
    print(f"Saving harmonised dataset to {output_file}")
    output_df.to_csv(output_file, index=False)
else:
    print("No processed data to save.")

print("Done.")
