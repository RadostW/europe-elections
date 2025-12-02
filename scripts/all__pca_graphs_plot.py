#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from tqdm import tqdm

# --- CONFIG ---
INPUT_CSV = "./pca_all_countries_with_nuts_urban_rural.csv"
OUT_DIR = Path("./plots_procrustes")
OUT_DIR.mkdir(exist_ok=True, parents=True)

# --- Load data ---
df = pd.read_csv(INPUT_CSV, dtype={"harmonised_code": str, "nuts3_code": str})

# Normalize typology strings for consistent legend keys
df["urban_rural_typology"] = (
    df["urban_rural_typology"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
)
# Optional: unify common forms
_map = {
    "predominantly urban": "Predominantly urban",
    "predominantly rural": "Predominantly rural",
    "intermediate": "Intermediate",
    "unknown": "Unknown",
    "nan": "Unknown"
}
df["urban_rural_typology"] = df["urban_rural_typology"].str.lower().replace(_map).where(
    df["urban_rural_typology"].notna(), "Unknown"
)

# Color palette (extend if there are other labels)
palette = {
    "Predominantly urban": "#1f77b4",
    "Intermediate": "#ff7f0e",
    "Predominantly rural": "#2ca02c",
    "Unknown": "#7f7f7f"
}

# --- Build reference (newest european) per country ---
refs = {}  # country -> DataFrame of reference (harmonised_code, pc1, pc2)
ref_metadata = {}  # country -> (election_date, election_type)

for country, g in df.groupby("country"):
    # Keep only European elections
    eur = g[g["election_type"].str.lower() == "european"]
    
    # Pick the newest election by sorting parsed date strings
    eur = eur.sort_values("election_date")
    ref_date = eur["election_date"].iloc[-1]
    ref_type = eur["election_type"].iloc[-1]
    ref_df = eur.query("election_date == @ref_date and election_type == @ref_type").copy()
    ref_df["harmonised_code"] = ref_df["harmonised_code"].astype(str)

    # Store reference PCs and metadata
    refs[country] = ref_df.set_index("harmonised_code")[["pc1", "pc2"]]
    ref_metadata[country] = (ref_date, ref_type)

# --- Procrustes helper (orthogonal) ---
def orthogonal_procrustes_rotation(A, B):
    """
    Compute orthogonal matrix R (2x2) that best maps B to A in least-squares sense:
    minimize || B R - A ||_F. Returns R.

    A and B are (n x 2) arrays (n observations x 2 dims).
    Both should be mean-centered.
    """
    # M = B^T A
    M = B.T.dot(A)
    U, s, Vt = np.linalg.svd(M)
    R = U.dot(Vt)
    
    return R

# --- Apply alignment per country/election ---
# We'll build a new DataFrame with rotated coordinates stored in columns pc1_r, pc2_r
rotated_rows = []

for (country, e_date, e_type), sub in tqdm(df.groupby(["country", "election_date", "election_type"]), desc="Aligning elections"):
    sub = sub.copy()
    sub["harmonised_code"] = sub["harmonised_code"].astype(str)

    ref_df = refs.get(country)
    
    # Find common regions by harmonised_code
    common = np.intersect1d(sub["harmonised_code"].unique(), ref_df.index.values)
    
    # Build matrices A (reference) and B (current) using the common harmonised_codes
    A = ref_df.loc[common, ["pc1", "pc2"]].to_numpy(dtype=float)
    # ensure rows in same order
    B = sub.set_index("harmonised_code").loc[common, ["pc1", "pc2"]].to_numpy(dtype=float)

    # Center both
    A_mean = A.mean(axis=0, keepdims=True)
    B_mean = B.mean(axis=0, keepdims=True)
    A_cent = A - A_mean
    B_cent = B - B_mean

    # Compute orthogonal transform R so that B_cent @ R ≈ A_cent

    transform = orthogonal_procrustes_rotation(A_cent, B_cent)

    # Apply transform to ALL rows in this election (center by B_mean of the matching rows)
    all_B = sub[["pc1", "pc2"]].to_numpy(dtype=float)
    # center all_B using B_mean (the same used above)
    all_B_cent = all_B - B_mean
    all_B_rot = all_B_cent.dot(transform)  # shape (m,2)

    # Re-center into reference frame: add A_mean so mapped coords are in reference origin
    all_B_rot_to_ref = all_B_rot + A_mean

    sub["pc1_r"] = all_B_rot_to_ref[:, 0]
    sub["pc2_r"] = all_B_rot_to_ref[:, 1]
    sub["aligned_to_reference"] = True
    rotated_rows.append(sub)

# Reconstruct DataFrame
rotated_df = pd.concat(rotated_rows, ignore_index=True)

# --- Plotting rotated results ---
# We will plot using pc1_r, pc2_r
plot_df = rotated_df.copy()

# Iterate and save one plot per election (aligned coords)
for (country, e_date, e_type), sub in tqdm(
    plot_df.groupby(["country", "election_date", "election_type"]),
    desc="Plotting elections"
):
    if sub.empty:
        continue

    # Use rotated columns
    x = sub["pc1_r"].to_numpy(dtype=float)
    y = sub["pc2_r"].to_numpy(dtype=float)

    # Compute 5th and 95th percentiles for both axes (rotated coords)
    q5_pc1, q95_pc1 = np.nanpercentile(x, [5, 95])
    q5_pc2, q95_pc2 = np.nanpercentile(y, [5, 95])

    quantile_range = max(abs(q5_pc1), abs(q95_pc1), abs(q5_pc2), abs(q95_pc2))
    lim = 1.5 * quantile_range
    if lim == 0 or not np.isfinite(lim):
        # fallback small range
        lim = 1.0

    fig, ax = plt.subplots(figsize=(7, 6))

    # Scatter
    sns.scatterplot(
        data=sub,
        x="pc1_r",
        y="pc2_r",
        hue="urban_rural_typology",
        palette=palette,
        alpha=0.85,
        edgecolor="white",
        s=70,
        ax=ax,
        legend=False,
    )

    ax.set_title(f"{country.capitalize()} {e_date} ({e_type})", fontsize=13, weight="bold")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal", adjustable="box")

    plt.tight_layout()
    fname = f"{country}_{e_date}_{e_type}.png".replace("/", "-")
    fig.savefig(OUT_DIR / fname, dpi=150)
    plt.close(fig)

print(f"\n✅ Saved aligned/scaled PCA plots to {OUT_DIR.resolve()}")
