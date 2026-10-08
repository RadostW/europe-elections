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


def test_election(election):

    WINNER_SHARE_ABSOLUTE_TOLEANCE = 5  # percentage points
    WINNER_VOTES_COUNT_RELATIVE_TOLERANCE = 15 / 100  # percent / 100

    expected = election
    observed = read_election_result(
        election["country"],
        election["election_date"],
        election["election_type"],
    )

    # assert observed["winner_votes"] / 1e6 == pytest.approx(
    #    expected["winner_votes"] / 1e6, rel=WINNER_VOTES_COUNT_RELATIVE_TOLERANCE
    # ), f'winner votes, {(expected["winner_votes"] - observed["winner_votes"])/1e3:.2f}k short of exp.'
    # assert observed["winner_share"] == pytest.approx(
    #    expected["winner_share"], abs=WINNER_SHARE_ABSOLUTE_TOLEANCE
    # ), f'winner share, {observed["winner_share"] / expected["winner_share"]:.2f} ratio'
    # assert observed["winner"].lower() == expected["winner"].lower(), "winner name"

    return {
        "winner_votes": 100
        * (observed["winner_votes"] - expected["winner_votes"])
        / expected["winner_votes"],
        "winner_share": (observed["winner_share"] - expected["winner_share"]),
    }


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import numpy as np

    scenarios = load_scenarios()

    tests = []

    for scenario in scenarios:

        election = scenario.values[0]

        test = test_election(election)
        test["id"] = scenario.id
        tests.append(test)

    df = pd.DataFrame(tests)

    FIGURE_WIDTH = 6
    FIGURE_HEIGHT = 5

    fig, axes = plt.subplots(
        figsize=(FIGURE_WIDTH, FIGURE_HEIGHT),
        ncols=4,
        constrained_layout=True,
        sharey=True,
        gridspec_kw={"wspace": 0},
    )

    df["country_code"] = df["id"].str.split("_").str[0]
    df["year"] = df["id"].str.split("_").str[1]
    df["c"] = df["country_code"].map(
        {
            "DE": "C0",
            "FR": "C1",
            "IT": "C2",
            "ES": "C3",
            "PL": "C4",
            "RO": "C5",
            "HU": "C6",
        }
    )

    df_left = df[:55].copy()
    df_left["y"] = list(reversed(range(len(df_left))))
    df_right = df[55:].copy()
    df_right["y"] = list(reversed(range(len(df_left))))

    axes[0].scatter(df_left["winner_votes"], df_left["y"], marker="o", c=df_left["c"])
    axes[1].scatter(df_left["winner_share"], df_left["y"], marker="D", c=df_left["c"])

    axes[2].scatter(
        df_right["winner_votes"], df_right["y"], marker="o", c=df_right["c"]
    )
    axes[3].scatter(
        df_right["winner_share"], df_right["y"], marker="D", c=df_right["c"]
    )

    for ax in [axes[0], axes[2]]:
        ax.set_xlim(-15, 5)
        ax.axvline(-5, zorder=-99, ls="--", c="#888")
        ax.axvline(+5, zorder=-99, ls="--", c="#888")

    for ax in [axes[1], axes[3]]:
        ax.set_xlim(-15, 5)
        ax.axvline(-2, zorder=-99, ls="--", c="#888")
        ax.axvline(2, zorder=-99, ls="--", c="#888")

    ll = df_left[~df_left["country_code"].duplicated()]
    rl = df_right[~df_right["country_code"].duplicated()]

    for ii, row in ll.iterrows():
        axes[0].annotate(
            row["country_code"],
            xy=(2, row["y"]),
            ha="center",
            va="center",
            fontsize=9,
        )
        axes[1].annotate(
            row["country_code"],
            xy=(3, row["y"]),
            ha="center",
            va="center",
            fontsize=9,
        )
    for ii, row in rl.iterrows():
        axes[2].annotate(
            row["country_code"],
            xy=(2, row["y"]),
            ha="center",
            va="center",
            fontsize=9,
        )        
        axes[3].annotate(
            row["country_code"],
            xy=(3, row["y"]),
            ha="center",
            va="center",
            fontsize=9,
        )        

    for ii, row in df_left.iterrows():
        if row["winner_votes"] < -5:
            axes[0].annotate(
                row["year"],
                xy=(row["winner_votes"] - 3, row["y"]),
                ha="center",
                va="center",
                fontsize=6,
            )
        if row["winner_share"] < -2:
            axes[1].annotate(
                row["year"],
                xy=(row["winner_share"] - 3, row["y"]),
                ha="center",
                va="center",
                fontsize=6,
            )


    for ii, row in df_right.iterrows():        
        if row["winner_votes"] < -5:
            axes[2].annotate(
                row["year"],
                xy=(row["winner_votes"] - 3, row["y"]),
                ha="center",
                va="center",
                fontsize=6,
            )
        if row["winner_share"] < -2:
            axes[3].annotate(
                row["year"],
                xy=(row["winner_share"] - 3, row["y"]),
                ha="center",
                va="center",
                fontsize=6,
            )

    axes[0].set_xlabel("$\Delta$ votes [%]")
    axes[2].set_xlabel("$\Delta$ votes [%]")

    axes[1].set_xlabel("$\Delta$ winner share [%]")
    axes[3].set_xlabel("$\Delta$ winner share [%]")

    for ax in axes:
        ax.tick_params(axis="y", left=False, labelleft=False)
        ax.set_ylabel("")

        ax.axvline(0, zorder=-99, ls="-", c="#888")
        ax.set_ylim(-1, 55)
        # ax.spines["left"].set_visible(False)

    plt.savefig('testing_votes.pdf')

    plt.show()
