import geopandas as gpd
from rapidfuzz.fuzz import ratio
from rapidfuzz.fuzz import token_set_ratio
from scipy.optimize import linear_sum_assignment
import numpy as np
import pandas as pd


def find_islands(df, distance):
    # Find geometries within 1 km of each other
    joined = gpd.sjoin(
        df[["locality_key", "geometry"]],
        df[["locality_key", "geometry"]],
        predicate="dwithin",
        distance=distance,
        how="left",
    )

    # Remove self-matches
    joined = joined[joined["locality_key_left"] != joined["locality_key_right"]]

    nonisland_keys = set(joined["locality_key_left"])
    return set(df["locality_key"]) - set(nonisland_keys)    


def merge_fuzzy(df_observed, df_reference, on_column):
        
    observed_names = df_observed[on_column].tolist()
    reference_names = df_reference[on_column].tolist()

    assert len(observed_names) > 0

    # Similarity matrix
    scores = np.array(
        [
            [0.5 * (ratio(a, b) + token_set_ratio(a, b)) for b in reference_names]
            for a in observed_names
        ]
    )

    # Hungarian algorithm minimizes cost, so use negative similarity
    row_ind, col_ind = linear_sum_assignment(-scores)

    fuzzy_matches = pd.DataFrame(
        {
            "observed": [observed_names[i] for i in row_ind],
            "reference": [reference_names[j] for j in col_ind],
            "score": [scores[i, j] for i, j in zip(row_ind, col_ind)],
        }
    )

    fuzzy_matches = fuzzy_matches.sort_values(by="score")

    observed_matched = df_observed.iloc[row_ind].reset_index(drop=True)
    reference_matched = (
        df_reference.iloc[col_ind].reset_index(drop=True).drop(columns=[on_column])
    )

    assert (
        len(set(observed_matched.columns).intersection(set(reference_matched.columns)))
        == 0
    )

    merged = pd.concat(
        [
            observed_matched,
            reference_matched,
        ],
        axis=1,
    )

    merged = gpd.GeoDataFrame(merged)

    return {
        "df": merged,
        "diagnostics": fuzzy_matches,
    }


def merge_with_gdf(
    df_localities,
    gdf_date_raw,
    columns_neighbourhood,
    match_column
):
    gdf_date = gdf_date_raw.copy()

    df_localities["locality_key"] = "ele_" + df_localities.index.astype(str).str.zfill(
        4
    )

    merged = gdf_date.merge(right=df_localities, on=match_column, how="inner")

    merged = merged.to_crs("EPSG:3035")
    merged["mistake"] = False

    for key, group in merged.groupby(columns_neighbourhood, dropna=False):
        if len(group) == 1:
            continue

        island_keys = find_islands(group, distance=1000)
        merged.loc[merged["locality_key"].isin(island_keys), "mistake"] = True

    merged.loc[merged["island_comune"], "mistake"] = False  # remove false positives
    merged_mistakes = merged[merged.mistake].copy()
    merged = merged[~merged.mistake].drop(columns="mistake")

    merged = merged[~merged["locality_key"].duplicated()] # drop multi-matched localities

    merged["match_method"] = "strict"

    if len(merged[merged["prov_name"] == "Valle d'Aosta/Vallée d'Aoste"]) < 5:
        # valle d'Aosta not in election data - drop from reference
        merged = merged[merged["prov_name"] != "Valle d'Aosta/Vallée d'Aoste"]
        gdf_date = gdf_date[gdf_date["prov_name"] != "Valle d'Aosta/Vallée d'Aoste"]

    strict_merged_lockeys = set(merged["locality_key"])
    df_localities_unmatched = df_localities[
        ~df_localities["locality_key"].isin(strict_merged_lockeys)
    ]

    strict_merged_refkeys = set(merged["terr_key"])
    df_reference_unmatched = gdf_date[~gdf_date["terr_key"].isin(strict_merged_refkeys)]

    print(
        f"unmatched count: {len(df_localities_unmatched)} / {len(df_localities)} = "
        f"{100 * len(df_localities_unmatched) / len(df_localities):.2f}"
    )

    
    merged_fuzzy_results = merge_fuzzy(
        df_observed=df_localities_unmatched,
        df_reference=df_reference_unmatched,
        on_column=match_column,
    )
    merged_fuzzy_df = merged_fuzzy_results["df"]
    merged_fuzzy_diagnostics = merged_fuzzy_results["diagnostics"]

    merged_fuzzy_df["match_method"] = "fuzzy"

    merged = pd.concat(
        [
            merged.to_crs("EPSG:3035"),
            merged_fuzzy_df[merged.columns].to_crs("EPSG:3035"),
        ]
    )

    merged["mistake"] = False
    for key, group in merged.groupby(columns_neighbourhood, dropna=False):                
        if len(group) == 1:
            continue
        
        island_keys = find_islands(group, distance=1000)
        merged.loc[merged["locality_key"].isin(island_keys), "mistake"] = True

    merged.loc[merged["island_comune"], "mistake"] = False  # remove false positives    
    merged = merged[~merged.mistake].drop(columns="mistake") # drop flying comunes
    

    strict_or_fuzzy_merged_lockeys = strict_merged_lockeys = set(merged["locality_key"])

    df_localities_unmatched_again = df_localities[
        ~df_localities["locality_key"].isin(strict_or_fuzzy_merged_lockeys)
    ]

    strict_or_fuzzy_merged_refkeys = set(merged["terr_key"])
    df_reference_unmatched_again = gdf_date[
        ~gdf_date["terr_key"].isin(strict_or_fuzzy_merged_refkeys)
    ]

    if len(df_localities_unmatched_again) > 0:
        # fallback for case when there are more localities than expected

        merged_fuzzy_results_again = merge_fuzzy(
            df_observed=df_localities_unmatched_again,
            df_reference=gdf_date,
            on_column=match_column,
        )
        merged_very_fuzzy_df = merged_fuzzy_results_again["df"]
        merged_very_fuzzy_diagnostics = merged_fuzzy_results_again["diagnostics"]

        merged_very_fuzzy_df["match_method"] = "very_fuzzy"

        merged = pd.concat(
            [
                merged.to_crs("EPSG:3035"),
                merged_very_fuzzy_df[merged.columns].to_crs("EPSG:3035"),
            ]
        )

    merged["mistake"] = False
    for key, group in merged.groupby(columns_neighbourhood, dropna=False):
        if len(group) == 1:
            continue

        island_keys = find_islands(group, distance=1000)
        merged.loc[merged["locality_key"].isin(island_keys), "mistake"] = True

    merged.loc[merged["island_comune"], "mistake"] = False  # remove false positives
    # merged = merged.drop(columns="mistake")

    if len(merged[merged["mistake"]]) > 0:
        print("[WARN] detected suspictious localities:")
        print(merged[merged["mistake"]].drop(columns="geometry").T)
    merged = merged.drop(columns="mistake")

    merged = merged[~merged["locality_key"].duplicated()]

    return {
        "matched_gdf": merged,
        "matched_mistakes": merged_mistakes,
        "matched_fuzzy": merged_fuzzy_diagnostics,
        "matched_very_fuzzy": None,
    }
