# try
# pytest --color=yes -vv tests/ | less -R
# for better visualisaiton

import pathlib

import matplotlib.pyplot as plt

import pandas as pd
import numpy as np
import pytest
import yaml

HERE = pathlib.Path(__file__).parent
DATA_DIR = HERE / ".." / "data" / "downloads"
COMPARISON_FILE = HERE / ".." / "data" / "all" / "metadata" / "population.csv"
SCENARIOS_FILE = HERE / "test_election_winner.yaml"


def pytest_generate_tests(metafunc):
    if "election" in metafunc.fixturenames:
        metafunc.parametrize(
            "election",
            load_scenarios(),
        )


def load_scenarios():
    with SCENARIOS_FILE.open() as f:
        data = yaml.safe_load(f)

    return [
        pytest.param(values, id=f"{test_name}") for test_name, values in data.items()
    ]


def read_voting_population(country, election_date):
    df_comp = pd.read_csv(COMPARISON_FILE, index_col=0)

    year_raw = float(str(election_date)[:4])
    year_clip = year_raw if year_raw >= 2014 else 2014
    year_clip = year_clip if year_clip < 2026 else 2025

    country_code = {
        "Germany": "DE",
        "France": "FR",
        "Italy": "IT",
        "Spain": "ES",
        "Poland": "PL",
        "Romania": "RO",
        "Hungary": "HU",
    }[country]

    mask = df_comp["nuts_3_code"].str.startswith(country_code)
    df_country = df_comp[mask]

    if year_raw < 2014:
        # Get 2014 and 2015 values for each NUTS-3 region
        df_2014 = df_country[df_country["year"] == 2014].set_index("nuts_3_code")
        df_2015 = df_country[df_country["year"] == 2015].set_index("nuts_3_code")

        # Linear extrapolation:
        # value(year) = value_2014 + (year - 2014) * (value_2015 - value_2014)
        voting_population = df_2014.copy()
        voting_population["year"] = year_raw
        voting_population["persons_20_and_older"] = (
            df_2014["persons_20_and_older"]
            + (year_raw - 2014)
            * (df_2015["persons_20_and_older"] - df_2014["persons_20_and_older"])
        )

        voting_population = voting_population.reset_index()

    else:
        voting_population = df_country[
            df_country["year"] == int(year_clip)
        ]
    
    nuts_level = 3
    # drop French remote islands
    voting_population = voting_population[~voting_population[f"nuts_{nuts_level}_code"].str.startswith("FRY")]
    # drop Spanish remote islands
    voting_population = voting_population[~voting_population[f"nuts_{nuts_level}_code"].str.startswith("ES7")]
    
    return voting_population


def read_election_eligibility(country, election_date, election_type):
    year_raw = float(str(election_date)[:4])

    election_date = str(election_date)
    csv_path = DATA_DIR / f"{country.lower()}_nuts_3.csv"

    # election_date,election_type,nuts_3_code,nuts_3_name,type,name,votes
    df = pd.read_csv(csv_path)

    election_dates = df["election_date"].drop_duplicates().values
    assert election_date in election_dates

    results_votes = df[
        (df["election_date"] == election_date) & (df["election_type"] == election_type)
    ]

    assert len(results_votes) > 0

    eligible_voters = results_votes[results_votes["name"] == "eligible_voters"][
        ["nuts_3_code", "nuts_3_name", "votes"]
    ]
    eligible_voters["year"] = year_raw
    
    

    nuts_level = 3
    # drop French remote islands
    eligible_voters = eligible_voters[~eligible_voters[f"nuts_{nuts_level}_code"].str.startswith("FRY")]
    # drop Spanish remote islands
    eligible_voters = eligible_voters[~eligible_voters[f"nuts_{nuts_level}_code"].str.startswith("ES7")]

    return eligible_voters


RELATIVE_TOLERANCE = 0.4
def test_election_eligible(election, assert_equal=True):

    expected = read_voting_population(
        election["country"],
        election["election_date"],
    )
    observed = read_election_eligibility(
        election["country"],
        election["election_date"],
        election["election_type"],
    )
    expected["persons_20_and_older"] = expected["persons_20_and_older"].astype(float)
    observed["votes"] = observed["votes"].astype(float)

    merged = pd.merge(expected, observed, on="nuts_3_code")

    assert len(merged) > 0

    if assert_equal:
        pd.testing.assert_frame_equal(
            merged[["nuts_3_code", "votes"]].rename(
                columns={"votes": "eligible_voters"}
            ),
            merged[["nuts_3_code", "persons_20_and_older"]].rename(
                columns={"persons_20_and_older": "eligible_voters"}
            ),
            check_exact=False,
            rtol=RELATIVE_TOLERANCE,
            atol=1000,
        )

    return merged


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import numpy as np

    scenarios = load_scenarios()
    for scenario in scenarios:
        election = scenario.values[0]
        merged_dataset = test_election_eligible(election, assert_equal=False)

        merged_dataset["error"] = (
            merged_dataset.votes - merged_dataset.persons_20_and_older
        ) / merged_dataset.persons_20_and_older

        plt.hist(merged_dataset["error"], range=(-2, 2), bins=200)
        plt.title(scenario.id)
        plt.show()
