#!/usr/bin/env python3
"""
Compute PCA per election (per country), add NUTS3 metadata and Urban/Rural typology.
Exports one long CSV:
  country, election_date, election_type, harmonised_code,
  nuts3_code, nuts3_name, urban_rural_typology, pc1, pc2
"""

import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from pathlib import Path
from tqdm import tqdm
import warnings

# --- CONFIG FILES ---
files = {
    "germany": "../data/downloads/germany.csv",
    "poland": "../data/downloads/poland.csv",
    "france": "../data/downloads/france.csv",
    "italy": "../data/downloads/italy.csv"
}

metadata_files = {
    "germany": "../data/downloads/germany_metadata.csv",
    "poland": "../data/downloads/poland_metadata.csv",
    "france": "../data/downloads/france_metadata.csv",
    "italy": "../data/downloads/italy_metadata.csv"
}

urban_rural_typology_file = "../data/all/metadata/nuts2024_urban_rural.csv"
OUT_PATH = Path("./pca_all_countries_with_nuts_urban_rural.csv")

# --- PCA helper ---
def compute_pca(df_votes):
    """Compute first two PCs of the region x party vote matrix."""
    if df_votes.shape[0] < 2 or df_votes.shape[1] < 1:
        return None
    df_votes = df_votes.loc[:, df_votes.var() > 0]
    if df_votes.shape[1] < 1:
        return None

    X = StandardScaler().fit_transform(df_votes.fillna(0))
    n_components = min(2, X.shape[0], X.shape[1])
    pca = PCA(n_components=n_components)
    comps = pca.fit_transform(X)

    df_res = pd.DataFrame(comps, index=df_votes.index, columns=[f"pc{i+1}" for i in range(n_components)])
    if n_components < 2:
        df_res["pc2"] = 0.0
    return df_res[["pc1", "pc2"]]

# --- Load Urban/Rural typology ---
try:
    ur_df = pd.read_csv(urban_rural_typology_file)
    ur_df = ur_df.rename(columns={
        "Country code": "country_code",
        "NUTS-3 Code": "nuts3_code",
        "Urban-Rural typology": "urban_rural_typology"
    })[["country_code", "nuts3_code", "urban_rural_typology"]]
    ur_df["nuts3_code"] = ur_df["nuts3_code"].astype(str)
except Exception as e:
    warnings.warn(f"Could not load urban/rural typology file: {e}")
    ur_df = None

# --- MAIN PROCESSING ---
all_results = []

for country, csv_path in files.items():
    print(f"\nProcessing {country} ...")

    # Load election CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        warnings.warn(f"Cannot read {csv_path}: {e}")
        continue

    required = {"election_date", "election_type", "harmonised_code", "type", "name", "votes"}
    if not required.issubset(df.columns):
        warnings.warn(f"{country} missing columns: {required - set(df.columns)}")
        continue

    # Load NUTS3 metadata
    meta_path = metadata_files.get(country)
    meta = None
    if meta_path and Path(meta_path).exists():
        meta = pd.read_csv(meta_path)                
        meta["nuts3_code"] = meta["nuts3_code"].astype(str)
    else:
        warnings.warn(f"No metadata for {country}: {meta_path}")

    # Filter to type==2
    df = df[df["type"] == 2].copy()
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0)

    # Process each election
    for (e_date, e_type), sub in tqdm(df.groupby(["election_date", "election_type"]),
                                      desc=f"{country} elections"):
        # Pivot to region x candidate
        pivot = (
            sub.groupby(["harmonised_code", "name"], as_index=False)["votes"]
            .sum()
            .pivot(index="harmonised_code", columns="name", values="votes")
            .fillna(0)
        )

        # --- Normalize to vote shares per region ---
        pivot = pivot.div(pivot.sum(axis=1), axis=0).fillna(0)

        pca_res = compute_pca(pivot)
        if pca_res is None:
            continue

        pca_res = pca_res.reset_index()
        pca_res["country"] = country
        pca_res["election_date"] = e_date
        pca_res["election_type"] = e_type

        # Merge with NUTS3 metadata
        if meta is not None:
            merged = pca_res.merge(meta, on="harmonised_code", how="left")
        else:
            merged = pca_res.copy()
            merged["nuts3_code"] = None
            merged["nuts3_name"] = None

        all_results.append(merged)

# --- Combine all countries ---
if all_results:
    out_df = pd.concat(all_results, ignore_index=True)

    # Add Urban-Rural typology
    if ur_df is not None:
        out_df = out_df.merge(
            ur_df,
            on="nuts3_code",
            how="left"
        )
    else:
        out_df["urban_rural_typology"] = None

    out_df = out_df[
        [
            "country",
            "election_date",
            "election_type",
            "harmonised_code",
            "nuts3_code",
            "nuts3_name",
            "urban_rural_typology",
            "pc1",
            "pc2",
        ]
    ]

    out_df.to_csv(OUT_PATH, index=False)
    print(f"\n✅ Saved PCA results with NUTS and Urban/Rural typology to {OUT_PATH} ({len(out_df)} rows)")
else:
    print("\n⚠️ No PCA results computed.")
