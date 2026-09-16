import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import pathlib
import numpy as np

here = pathlib.Path(__file__).resolve().parent

STYLE_FILE = here / "elections.mplstyle"
plt.style.use(STYLE_FILE)
plt.rcParams.update({"lines.marker": ""})  # no default markers

# --- CONFIG FILES WITH FOLDER PATH ---
files = {
    "germany": "../data/downloads/germany.csv",
    "france": "../data/downloads/france.csv",
    "italy": "../data/downloads/italy.csv",
    "spain": "../data/downloads/spain.csv",
    "poland": "../data/downloads/poland.csv",
    "romania": "../data/downloads/romania.csv",
    "hungary": "../data/downloads/hungary.csv",
}

renames = {
    "bundestag": "parliament",
    "camera": "parliament",
    "congresso": "parliament",
    "sejm": "parliament",
    "house": "parliament",
    "parliament": "parliament",
    "president_a": "president I",
    "president_b": "president II",
}

meta_dict = dict()
for country, paths in files.items():
    # Load CSV
    df = pd.read_csv(here / paths)

    coverage = (
        df[["election_date", "election_type"]]
        .drop_duplicates()
        .sort_values(by=["election_type", "election_date"])
    )
    country_dict = dict()
    for et in df.election_type.unique():

        label = renames.get(et,et)

        country_dict[label] = list(
            coverage[coverage.election_type == et].election_date.values
        )

    meta_dict[country] = country_dict


# Plotting ======================

FIG_WIDTH = 7
FIG_HEIGHT = 5

fig, ax = plt.subplots(
    1,
    1,
    figsize=(FIG_WIDTH, FIG_HEIGHT),
    constrained_layout=True,
)


i = 0
j = 0

yticks = []
ytick_labels = []

for country, coverage in reversed(sorted(meta_dict.items())):

    for et, dates in reversed(sorted(coverage.items())):
        years = np.array([int(date[:4]) for date in dates])
        months = np.array([int(date[5:7]) for date in dates])
        xlist = years + months / 12
        ylist = [i + j] * len(xlist)

        yticks.append(i + j)        
        ytick_labels.append(et)

        ax.scatter(xlist, ylist, c=f"C{j}",s=30)
        i = i + 1

    yticks.append(i + j)
    ytick_labels.append(country.title())
    i = i + 1

    j = j + 1


ax.set_xlim(2000, None)
ax.set_yticks(yticks, ytick_labels)

plt.show()
