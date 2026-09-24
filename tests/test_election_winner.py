# try
# pytest --color=yes -vv tests/ | less -R
# for better visualisaiton

from pathlib import Path

import pandas as pd
import pytest
import yaml

HERE = Path(__file__).parent
SCENARIOS_FILE = HERE / "test_election_winner.yaml"
DATA_DIR = HERE / ".." / "data" / "downloads"


def load_scenarios():
    with SCENARIOS_FILE.open() as f:
        data = yaml.safe_load(f)

    return [
        pytest.param(values, id=f"{test_name}") for test_name, values in data.items()
    ]


def test_scenarios_complete():

    with SCENARIOS_FILE.open() as f:
        data = yaml.safe_load(f)

    countries = set(
        str(values["country"].lower()) for test_name, values in data.items()
    )

    for country in countries:
        csv_path = DATA_DIR / f"{country}_nuts_1.csv"
        df = pd.read_csv(csv_path)
        election_dates = set(df["election_date"].drop_duplicates().values)

        scenario_dates = set(
            str(values["election_date"])
            for test_name, values in data.items()
            if values["country"].lower() == country
        )

        assert (
            election_dates - scenario_dates
        ) == set(), (
            f"imperfect coverage: {country}, N={len(election_dates - scenario_dates)}"
        )
        assert (
            scenario_dates - election_dates
        ) == set(), (
            f"testing non-election: {country}, N={len(scenario_dates - election_dates)}"
        )


def pytest_generate_tests(metafunc):
    if "election" in metafunc.fixturenames:
        metafunc.parametrize(
            "election",
            load_scenarios(),
        )


def read_election_result(country, election_date, election_type):
    election_date = str(election_date)
    csv_path = DATA_DIR / f"{country.lower()}_nuts_1.csv"

    # election_date,election_type,nuts_1_code,nuts_1_name,type,name,votes
    df = pd.read_csv(csv_path)

    election_dates = df["election_date"].drop_duplicates().values
    assert election_date in election_dates

    results_votes = (
        df[
            (df["election_date"] == election_date)
            & (df["election_type"] == election_type)
        ]
        .groupby("name")
        .agg(
            votes=("votes", "sum"),
            type=("type", "first"),
        )
    )

    assert len(results_votes) > 0

    total_votes = results_votes.loc["issued_ballots", "votes"]
    candidates = results_votes[results_votes["type"] == 2]

    winner_name = candidates["votes"].idxmax()
    winner_votes = candidates.loc[winner_name, "votes"]

    return {
        "winner": winner_name,
        "winner_share": 100 * winner_votes / total_votes,
        "winner_votes": winner_votes,
    }


def test_election_soft(election):

    WINNER_SHARE_ABSOLUTE_TOLEANCE = 5  # percentage points
    WINNER_VOTES_COUNT_RELATIVE_TOLERANCE = 15 / 100  # percent / 100

    expected = election
    observed = read_election_result(
        election["country"],
        election["election_date"],
        election["election_type"],
    )

    assert observed["winner_votes"] / 1e6 == pytest.approx(
        expected["winner_votes"] / 1e6, rel=WINNER_VOTES_COUNT_RELATIVE_TOLERANCE
    ), f'winner votes, {(expected["winner_votes"] - observed["winner_votes"])/1e3:.2f}k short of exp.'
    assert observed["winner_share"] == pytest.approx(
        expected["winner_share"], abs=WINNER_SHARE_ABSOLUTE_TOLEANCE
    ), f'winner share, {observed["winner_share"] / expected["winner_share"]:.2f} ratio'
    assert observed["winner"].lower() == expected["winner"].lower(), "winner name"


def test_election_hard(election):

    WINNER_SHARE_ABSOLUTE_TOLEANCE = 2  # percentage points
    WINNER_VOTES_COUNT_RELATIVE_TOLERANCE = 5 / 100  # percent / 100

    expected = election
    observed = read_election_result(
        election["country"],
        election["election_date"],
        election["election_type"],
    )

    assert observed["winner_votes"] / 1e6 == pytest.approx(
        expected["winner_votes"] / 1e6, rel=WINNER_VOTES_COUNT_RELATIVE_TOLERANCE
    ), f'winner votes, {(expected["winner_votes"] - observed["winner_votes"])/1e3:.2f}k short of exp.'
    assert observed["winner_share"] == pytest.approx(
        expected["winner_share"], abs=WINNER_SHARE_ABSOLUTE_TOLEANCE
    ), f'winner share, {observed["winner_share"] / expected["winner_share"]:.2f} ratio'
    assert observed["winner"].lower() == expected["winner"].lower(), "winner name"
