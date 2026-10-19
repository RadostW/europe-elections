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
    "germany": "../data/downloads/germany_nuts_1.csv",
    "france": "../data/downloads/france_nuts_1.csv",
    "italy": "../data/downloads/italy_nuts_1.csv",
    "spain": "../data/downloads/spain_nuts_1.csv",
    "poland": "../data/downloads/poland_nuts_1.csv",
    "romania": "../data/downloads/romania_nuts_1.csv",
    "hungary": "../data/downloads/hungary_nuts_1.csv",
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

# FIG_WIDTH = 7
# FIG_HEIGHT = 5

# fig, ax = plt.subplots(
#     1,
#     1,
#     figsize=(FIG_WIDTH, FIG_HEIGHT),
#     constrained_layout=True,
# )


# i = 0
# j = 0

# yticks = []
# ytick_labels = []

# for country, coverage in reversed(sorted(meta_dict.items())):

#     for et, dates in reversed(sorted(coverage.items())):
#         years = np.array([int(date[:4]) for date in dates])
#         months = np.array([int(date[5:7]) for date in dates])
#         xlist = years + months / 12
#         ylist = [i + j] * len(xlist)

#         yticks.append(i + j)        
#         ytick_labels.append(et)

#         ax.scatter(xlist, ylist, c=f"C{j}",s=30)
#         i = i + 1

#     yticks.append(i + j)
#     ytick_labels.append(country.title())
#     i = i + 1

#     j = j + 1


# ax.set_xlim(2000, None)
# ax.set_yticks(yticks, ytick_labels)

# plt.show()

from collections import defaultdict

# Map election types to letters
election_codes = {
    'european': 'e',
    'parliament': 'l',
    'president I': 'p',
    'president II': 'p',
}

# Map country names to column abbreviations
country_codes = {
    'germany': 'DE',
    'france': 'FR',
    'italy': 'IT',
    'spain': 'ES',
    'poland': 'PL',
    'romania': 'RO',
    'hungary': 'HU',
}

# Collect elections by country and year
data = defaultdict(lambda: defaultdict(set))

for country, elections in meta_dict.items():
    code = country_codes[country]

    for election_type, dates in elections.items():
        letter = election_codes[election_type]

        for date in dates:
            year = int(date[:4])
            data[year][code].add(letter)

# Create the DataFrame
years = range(1992, 2027)

df = pd.DataFrame(
    {
        code: {
            year: '+'.join(sorted(data[year][code]))
            for year in years
            if data[year][code]
        }
        for code in country_codes.values()
    }
)

# Replace missing values with empty strings
df = df.reindex(years).fillna('')

df.index.name = 'Year'

print(df)

print({k:{t:len(s) for t,s in v.items()} for k,v in meta_dict.items()})