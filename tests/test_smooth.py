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

countries = ["Hungary"]

for country in countries:
    csv_path = DATA_DIR / f"{country.lower()}_nuts_3.csv"
    df = pd.read_csv(csv_path)
    df_ev = df[(df.type == 0) & (df.election_type == "european")]

    election_dates = set(df["election_date"].drop_duplicates().values)


for code in df_ev.nuts_3_code.drop_duplicates():
    q = df_ev[df_ev.nuts_3_code == code]
    x = q["election_date"].str[:4].astype(int)
    y = q["votes"] / q["votes"].mean()
    # y = q["votes"]

    x_adj = x
    y_adj = y - np.polyval(np.polyfit(x, y, 1), x)
    y_fit = np.polyval(np.polyfit(x, y, 1), x)
    plt.plot(x_adj, y_adj)

plt.show()
