import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from itertools import combinations, combinations_with_replacement
import pathlib

# Define paths
here = pathlib.Path(__file__).resolve().parent
files = {
    "Germany": here / "../data/downloads/germany.csv",
    "Poland": here / "../data/downloads/poland.csv",
    "France": here / "../data/downloads/france.csv",
}

# Load datasets into a dict
data_dict = {country: pd.read_csv(path) for country, path in files.items()}

# Store PC1 per country per election
pc1_values = {}

for country, df in data_dict.items():

    df = df[~(df["election_type"] == "bunddestag")]

    # Keep only "eligible voters" to check completeness
    eligible = df[df["name"] == "eligible_voters"]
    counts = (
        eligible.groupby(["harmonised_code", "election_date"])
        .size()
        .unstack(fill_value=0)
    )
    complete_regions = counts.index[(counts == 1).all(axis=1)]

    df = df[df["harmonised_code"].isin(complete_regions)]

    elections = df["election_date"].unique()    

    pc1_values[country] = {}

    for election in elections:        
        df_election = df[(df["election_date"] == election) & (df["type"] == 2)].copy()

        # Aggregate small parties coded as 'DIV' per region
        df_election = df_election.groupby(["harmonised_code", "name"], as_index=False)[
            "votes"
        ].sum()

        # Now pivot: regions as rows, parties as columns
        pivot = df_election.pivot(
            index="harmonised_code", columns="name", values="votes"
        ).fillna(0)

        # Standardize and compute PCA
        X_scaled = StandardScaler().fit_transform(pivot)
        pca = PCA(n_components=1)
        pc1 = pca.fit_transform(X_scaled)
        pc1_values[country][election] = pd.Series(pc1.flatten(), index=pivot.index)


# Compute correlations and days between elections
correlations = []

for country, elections_dict in pc1_values.items():
    election_dates = sorted(elections_dict.keys())
    # for e1, e2 in combinations(election_dates, 2):
    for e1, e2 in combinations_with_replacement(election_dates, 2):
        pc1_1 = elections_dict[e1]
        pc1_2 = elections_dict[e2]
        corr = pc1_1.corr(pc1_2)

        # Convert string dates to datetime
        d1 = pd.to_datetime(e1, format="%Y_%m_%d")
        d2 = pd.to_datetime(e2, format="%Y_%m_%d")
        days_diff = (d2 - d1).days

        correlations.append(
            {
                "country": country,
                "election_1": e1,
                "election_2": e2,
                "days_diff": days_diff,
                "correlation": corr,
            }
        )

corr_df = pd.DataFrame(correlations)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Convert days to years
corr_df["years_diff"] = corr_df["days_diff"] / 365.25

plt.figure(figsize=(10, 6))
markers = {"Germany": "o", "Poland": "s", "France": "^"}
colors = {"Germany": "C0", "Poland": "C1", "France": "C2"}

# Scatter points
for country in corr_df["country"].unique():
    sub = corr_df[corr_df["country"] == country]
    plt.scatter(
        sub["years_diff"],
        sub["correlation"],
        label=country,
        marker=markers[country],
        color=colors[country],
        alpha=0.2,
    )


bin_size = 2
max_years = int(corr_df["years_diff"].max()) + bin_size
bins = np.arange(0, max_years + bin_size, bin_size)

from statsmodels.nonparametric.smoothers_lowess import lowess

for country in corr_df["country"].unique():
    sub = corr_df[corr_df["country"] == country]
    # bin_means_x = []
    # bin_means_y = []
    # for i in range(len(bins) - 1):
    #     mask = (sub["years_diff"] >= bins[i]) & (sub["years_diff"] < bins[i + 1])
    #     if mask.any():
    #         bin_means_x.append(sub.loc[mask, "years_diff"].mean())
    #         bin_means_y.append(sub.loc[mask, "correlation"].mean())
    # plt.plot(bin_means_x, bin_means_y, color=colors[country], lw=2)

    lowess_smoothed = lowess(sub["correlation"], sub["years_diff"], frac=0.3, it=5)
    plt.plot(lowess_smoothed[:, 0], lowess_smoothed[:, 1], color=colors[country], lw=2, linestyle="-", label=f"{country} (LOWESS)")


plt.xlabel("Delay [years]")
plt.ylabel("PC1 correlation")
plt.legend()
plt.show()
