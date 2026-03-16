#!/usr/bin/env python3
"""
Compute PCA variance share for each country-election pair.
Exports one long CSV:
  country, election_date, election_type, pca_var_pc1, pca_var_pc2, pca_var_pc3
"""

import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from pathlib import Path
from tqdm import tqdm
import warnings
import pathlib

here = pathlib.Path(__file__).resolve().parent

# --- CONFIG FILES ---
files = {
    "germany": "../data/downloads/germany.csv",
    "poland": "../data/downloads/poland.csv",
    "france": "../data/downloads/france.csv",
    "italy": "../data/downloads/italy.csv",
    "spain": "../data/downloads/spain.csv",
}

OUT_PATH = Path("./pca_variance_share_all_countries.csv")


# --- PCA variance helper ---
def compute_pca_variance(df_votes):
    """
    Compute explained variance ratio for the first 3 PCs
    from region x party vote-share matrix.
    Returns dict with variance ratios.
    """

    if "cdu" in df_votes.columns and "csu" in df_votes.columns:
        df_votes["cdu_csu"] = df_votes["cdu"] + df_votes["csu"]
        df_votes.drop(columns=["cdu", "csu"])

    if df_votes.shape[0] < 2 or df_votes.shape[1] < 1:
        return None

    # Remove zero-variance parties
    df_votes = df_votes.loc[:, df_votes.var() > 0]
    if df_votes.shape[1] < 1:
        return None

    # Standardize
    # X = StandardScaler().fit_transform(df_votes.fillna(0))
    X = df_votes.fillna(0)

    n_components = min(3, X.shape[0], X.shape[1])
    pca = PCA(n_components=n_components)
    pca.fit(X)

    # Fill missing PCs with 0 variance if fewer than 3 extracted
    vars_out = list(pca.explained_variance_ratio_)
    while len(vars_out) < 3:
        vars_out.append(0.0)

    return {
        "pca_var_pc1": vars_out[0],
        "pca_var_pc2": vars_out[1],
        "pca_var_pc3": vars_out[2],
    }


# --- MAIN PROCESSING ---
all_rows = []

for country, csv_path in files.items():

    print(f"\nProcessing {country} ...")

    # Load election CSV
    try:
        df = pd.read_csv(here / csv_path)
    except Exception as e:
        warnings.warn(f"Cannot read {csv_path}: {e}")
        continue

    required = {
        "election_date",
        "election_type",
        "harmonised_code",
        "type",
        "name",
        "votes",
    }
    if not required.issubset(df.columns):
        warnings.warn(f"{country} missing columns: {required - set(df.columns)}")
        continue

    # Filter to type == 2 (regions)
    df = df[df["type"] == 2].copy()
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0)

    # Group elections
    for (e_date, e_type), sub in tqdm(
        df.groupby(["election_date", "election_type"]), desc=f"{country} elections"
    ):

        # Build region x party matrix
        pivot = (
            sub.groupby(["harmonised_code", "name"], as_index=False)["votes"]
            .sum()
            .pivot(index="harmonised_code", columns="name", values="votes")
            .fillna(0)
        )

        # Convert to vote shares
        pivot = pivot.div(pivot.sum(axis=1), axis=0).fillna(0)

        if e_type == "president_b":
            continue
        res = compute_pca_variance(pivot)
        if res is None:
            continue

        res["country"] = country
        res["election_date"] = e_date
        res["election_type"] = e_type

        all_rows.append(res)

df_all = pd.DataFrame.from_dict(all_rows)
df_all["year"] = df_all.election_date.str[:4].astype(int)
df_all["month"] = df_all.election_date.str[5:7].astype(int)
df_all["time"] = df_all["year"] + ((df_all["month"] - 1) / 12)


import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# PC definitions: (column_name, linestyle, short_label)
pcs = [
    ("pca_var_pc1", "-", "PC1", 0),
    ("pca_var_pc2", "--", "PC2", 1),
    ("pca_var_pc3", ":", "PC3", 2),
]

plt.figure(figsize=(11, 6))
ax = plt.gca()

# color per country (consistent order)
countries = sorted(df_all["country"].unique())
color_map = {c: f"C{i}" for i, c in enumerate(countries)}

# Plot: nested groupby country -> election_type
for country, df_c in df_all.groupby("country"):
    country_color = color_map[country]

    for election_type, g in df_c.groupby("election_type"):
        g = g.sort_values("time")
        x = g["time"]

        # inner loop over PCs avoids repetition
        for pc_col, ls, _pc_label, pc_level in pcs:
            y = g[pc_col]

            alpha_step = 0.4

            # draw only the line (transparent)
            ax.plot(
                x,
                y,
                linestyle=ls,
                color=country_color,
                alpha=1 - alpha_step * pc_level,
                linewidth=2,
            )

            # draw only the markers (opaque)
            ax.scatter(
                x,
                y,
                marker="o",
                s=40,
                facecolors=country_color,
                edgecolors="black",
                linewidths=0.5,
                alpha=1 - alpha_step * pc_level,
                zorder=3,
            )


# Country legend handles
country_handles = [
    Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=color_map[c],
        markeredgecolor="k",
        markersize=8,
        label=c,
    )
    for c in countries
]

# PC legend handles
pc_handles = [
    Line2D([0], [0], color="k", linestyle=ls, lw=2, label=label)
    for (_col, ls, label, level) in pcs
]

# ---- FUSE LEGENDS INTO ONE ----
all_handles = country_handles + pc_handles
all_labels = [h.get_label() for h in all_handles]

ax.legend(
    handles=all_handles,
    labels=all_labels,
    # title="Country / Principal Component",
    loc="upper left",
    bbox_to_anchor=(1.02, 1.0),
)


ax.set_xlabel("Time")
ax.set_ylabel("Variance share")
# ax.set_title("PCA variance share over time — lines colored by country\n(transparent lines, opaque markers)")
plt.tight_layout()
plt.show()
