import pathlib
import json
import pandas as pd
import numpy as np
import unidecode


def from_json(path):
    with open(path) as fp:
        return json.load(fp)


here = pathlib.Path(__file__).resolve().parent

files_to_parse = (here / "../data/romania/raw_datasets/judete").resolve().glob("*.json")
nuts_path = here / "../data/romania/metadata/nuts2024_romania.csv"

nuts = pd.read_csv(nuts_path)
nuts = nuts[nuts["NUTS level"] == 3]

records = None

for file in files_to_parse:
    q = from_json(file)

    county_name = q["scope"]["countyName"]
    county_id = q["scope"]["countyId"]

    election_date = q["meta"]["date"][:10]

    if election_date == "2014-05-25":
        print("[WARN] Skipping malformed data: election_date == 2014-05-25")
        continue

    election_type_raw = q["meta"]["type"]  # eg 'president'
    ballot_type = q["meta"]["ballot"]  # eg 'Turul 1'

    if election_type_raw == "president":
        if ballot_type == "Turul 1":
            election_type = "president_a"
        elif ballot_type == "Turul 2":
            election_type = "president_b"
        else:
            raise NotImplementedError
    else:
        election_type = election_type_raw

    eligible_voters = q["turnout"]["eligibleVoters"]
    total_votes = q["turnout"]["totalVotes"]

    # ,election_date,election_type,harmonised_code,harmonised_name,type,name,votes
    election_table = pd.DataFrame.from_dict(
        {
            "election_date": [election_date, election_date],
            "election_type": [election_type, election_type],
            "harmonised_code": [county_id, county_id],
            "harmonised_name": [county_name, county_name],
            "type": [0, 1],
            "name": ["eligible_voters", "issued_ballots"],
            "party_name": ["eligible_voters", "issued_ballots"],
            "votes": [eligible_voters, total_votes],
        }
    )

    candidate_results = []
    for row in q["results"]["candidates"]:
        candidate_name = row.get("shortName", row["name"])
        party_name = row.get("partyName", "")
        candidate_votes = row["votes"]

        candidate_results.append(
            {
                "election_date": election_date,
                "election_type": election_type,
                "harmonised_code": county_id,
                "harmonised_name": county_name,
                "type": 2,
                "name": candidate_name,
                "party_name": party_name,
                "votes": candidate_votes,
            }
        )

    election_table = pd.concat(
        [election_table, pd.DataFrame.from_records(candidate_results)]
    )

    if records is None:
        records = election_table
    else:
        records = pd.concat([records, election_table])

records = records.reset_index()

nuts["harmonised_name"] = nuts["NUTS label"].apply(lambda x: unidecode.unidecode(x))

output = pd.merge(
    left=records,
    right=nuts[["NUTS Code", "NUTS label", "harmonised_name"]],
    left_on="harmonised_name",
    right_on="harmonised_name",
    how="left",
).rename(
    columns={
        "NUTS Code": "nuts3_code",
        "NUTS label": "nuts3_name",
    }
)
output["election_type"] = output["election_type"].replace(
    to_replace="european_parliament", value="european"
)

output["harmonised_code"] = output["nuts3_code"]

output_path = (
    here
    / "../data/romania/harmonised/judete/romania__long.csv"
)
output.to_csv(output_path)