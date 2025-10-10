import pandas as pd
import pathlib
import yaml
import unicodedata
import numpy as np

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------
here = pathlib.Path(__file__).resolve().parent

election_file = here / "../data/france/raw_datasets/departament/france__departament.csv"
eligible_file = (
    here / "../data/france/raw_datasets/departament/france__departament_eligible.csv"
)
output_file = here / "../data/france/harmonised/departament/france__long.csv"

config_path = here / "../data/france/raw_datasets/metadata/replacement_rules.yaml"

# ---------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------
print(f"Loading data from {election_file}")
df_votes = pd.read_csv(election_file, low_memory=False)
df_eligible = pd.read_csv(eligible_file, low_memory=False)

with open(config_path.resolve(), "r", encoding="utf-8") as in_file:
    try:
        config = yaml.safe_load(in_file)
    except yaml.YAMLError as exc:
        print(exc)
        raise

import pandas as pd


# ---------------------------------------------------------------------
# Construct name dictionary, taking the first name for each code
# ---------------------------------------------------------------------

df_names = df_eligible[["department_code", "department_name"]].copy()
df_names = df_names[df_names["department_name"] != "missing"]


# # Optional: normalize to ASCII for consistency (not strictly needed if just taking first)
# def normalize_name(name):
#     ascii_name = (
#         unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("ASCII")
#     )
#     return ascii_name


# Construct dictionary by taking the first occurrence of each department_code
code_to_name = (
    df_names.drop_duplicates(subset="department_code")
    .set_index("department_code")["department_name"]
    .to_dict()
)

code_to_name["ZT"] = "Special"
code_to_name["ZY"] = "Special"
code_to_name["977"] = "Saint-Barthélemy"
code_to_name["99"] = "Special"

# ---------------------------------------------------------------------
# Identify election types (example: extract from election_id)
# ---------------------------------------------------------------------
df_votes["election_type"] = df_votes["election_id"].str.extract(
    r"_(\D+)_", expand=False
)
df_votes["election_year"] = df_votes["election_id"].str.extract(
    r"(\d{4})", expand=False
)
df_votes["round_string"] = df_votes["election_id"].str.extract(
    r"_(t\d+)$", expand=False
)

# ---------------------------------------------------------------------
# Prepare accumulator for processed data
# ---------------------------------------------------------------------
processed_chunks = []

# ---------------------------------------------------------------------
# Loop over election types
# ---------------------------------------------------------------------
for election_id, subset in df_votes.groupby("election_id"):

    election_type_short = subset["election_type"].iloc[0]
    election_year = subset["election_year"].iloc[0]
    election_id = subset["election_id"].iloc[0]
    round_string = subset["round_string"].iloc[0]

    print(f"Processing election type: {election_type_short} ({len(subset)} rows)")
    # Example: handle only presidential elections
    if election_type_short in ["pres", "euro"]:

        # Lookup date from config
        election_date = config["election_id_to_date"][election_id]

        # Determine full election type (add suffix for round)
        if election_type_short == "pres":
            election_type = "president" + "_" + ("a" if round_string == "t1" else "b")
        elif election_type_short == "euro":
            election_type = "european"

        def get_department_name(code):
            return code_to_name[code]

        subset_eligible = df_eligible[(df_eligible["election_id"] == election_id)]

        if len(subset_eligible) == 0:
            raise ValueError("Empty eligible voters dataset")

        harmonised_eligible = pd.DataFrame(
            {
                "election_date": election_date,
                "election_type": election_type,
                "harmonised_code": "M_"
                + subset_eligible["department_code"].astype(str),
                "harmonised_name": (subset_eligible["department_code"]).apply(
                    get_department_name
                ),
                "type": 0,  # 0 = eligible voters
                "name": "eligible_voters",
                "votes": subset_eligible["eligible_voters"],
            }
        )

        harmonised_issued = pd.DataFrame(
            {
                "election_date": election_date,
                "election_type": election_type,
                "harmonised_code": "M_"
                + subset_eligible["department_code"].astype(str),
                "harmonised_name": (subset_eligible["department_code"]).apply(
                    get_department_name
                ),
                "type": 1,  # 1 = issued ballots
                "name": "issued_ballots",
                "votes": subset_eligible["voters"],
            }
        )

        if election_type_short == "pres":
            harmonised_votes = pd.DataFrame(
                {
                    "election_date": election_date,
                    "election_type": election_type,
                    "harmonised_code": "M_" + subset["department_code"].astype(str),
                    "harmonised_name": (subset["department_code"]).apply(
                        get_department_name
                    ),
                    "type": 2,  # 2 = votes for candidates
                    "name": subset["last_name"]
                    .fillna("")
                    .str.title()
                    .str.replace(" ", "", regex=False),
                    "votes": subset["votes"],
                }
            )
        elif election_type_short == "euro":

            # fix missing
            if election_id == "2019_euro_t1":
                subset["political_orientation"] = subset["list_label_short"].map(
                    config["list_label_short_to_political_orientation"]
                )

            harmonised_votes = pd.DataFrame(
                {
                    "election_date": election_date,
                    "election_type": election_type,
                    "harmonised_code": "M_" + subset["department_code"].astype(str),
                    "harmonised_name": (subset["department_code"]).apply(
                        get_department_name
                    ),
                    "type": 2,  # 2 = votes for candidates
                    "name": subset["political_orientation"],
                    "votes": subset["votes"],
                }
            )

        # Combine the three into a single DataFrame first
        chunk_df = pd.concat(
            [harmonised_eligible, harmonised_issued, harmonised_votes],
            ignore_index=True,
        )
        chunk_df = chunk_df.sort_values(by="harmonised_code")
        processed_chunks.append(chunk_df)

    elif election_type_short == "cant":
        pass
    else:
        pass
        # print("AAAA!")

# ---------------------------------------------------------------------
# Combine, validate and save
# ---------------------------------------------------------------------
if not processed_chunks:
    print("No processed data to save.")
    raise ValueError("No data")

output_df = pd.concat(processed_chunks, ignore_index=True)
output_df = output_df.sort_values(
    by=["election_date", "harmonised_code", "type"]
).reset_index(drop=True)

# Step 1: Aggregate votes by election and candidate
agg = (
    output_df[output_df["type"] == 2]
    .groupby(["election_date", "election_type", "name"], as_index=False)["votes"]
    .sum()
)

# Step 2: Compute total votes and candidate percentages
agg["total_votes"] = agg.groupby(["election_date", "election_type"])["votes"].transform(
    "sum"
)
agg["pct"] = agg["votes"] / agg["total_votes"] * 100

# Step 3: Determine the winner per election
winners = (
    agg.sort_values(
        ["election_date", "election_type", "pct"], ascending=[True, True, False]
    )
    .groupby(["election_date", "election_type"])
    .first()
    .reset_index()
)

# Step 4: Compare to expected results in config
for _, row in winners.iterrows():
    date = row["election_date"]
    election_type = row["election_type"]
    date_string = f"{date}"

    if date_string not in config["results_checks"]:
        raise KeyError(f"No config entry found for {date_string}")

    expected = config["results_checks"][date_string]
    expected_winner = expected["winner"]
    expected_result = expected["result"]

    actual_winner = row["name"]
    actual_pct = row["pct"]

    # Check if results match expected
    if (actual_winner != expected_winner) or not np.isclose(
        actual_pct, expected_result, rtol=1e-03, atol=0.25
    ):
        # Recompute detailed results for this election
        election_results = (
            agg[
                (agg["election_date"] == date) & (agg["election_type"] == election_type)
            ]
            .sort_values("pct", ascending=False)
            .loc[:, ["name", "votes", "pct"]]
        )

        # Build debug info string
        details = "\n".join(
            f"    {n:<20} {v:>10,d}  ({p:6.2f}%)"
            for n, v, p in election_results.itertuples(index=False)
        )

        raise AssertionError(
            f"\nResult mismatch for {date_string} ({election_type}):\n"
            f"  Expected: {expected_winner} ({expected_result:.2f}%)\n"
            f"  Got     : {actual_winner} ({actual_pct:.2f}%)\n"
            f"  Full results:\n{details}"
        )

print(f"Sorting")
output_df = output_df.sort_values(
    by=["election_date", "harmonised_code", "type", "votes"],
    ascending=[True, True, True, False],  # example: votes descending
)


print(f"Saving harmonised dataset to {output_file}")
output_df.to_csv(output_file)
