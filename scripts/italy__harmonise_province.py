# Read README.md in ../data/italy to understand the data better

import yaml
import pathlib
import pandas as pd
import geopandas as gpd
import re
import unidecode
import matplotlib.pyplot as plt

from itertools import cycle
from matplotlib import colormaps


@pd.api.extensions.register_series_accessor("normalize_string")
class NormalizeStringAccessor:
    def __init__(self, s):
        self._obj = s

    def __call__(self):
        return (
            self._obj.astype(str)
            .map(unidecode.unidecode)
            .str.lower()
            .str.replace(r"[^a-z ]", "", regex=True)
            .str.strip()
        )


here = pathlib.Path(__file__).resolve().parent

config_path = (
    here / "../data/italy/raw_datasets/metadata/replacement_rules_comunes.yaml"
)

files_to_parse = sorted(
    list((here / "../data/italy/raw_datasets/province").resolve().glob("*.csv"))
)

comune_geodata_path = (
    here
    / ".."
    / "data"
    / "italy"
    / "raw_datasets"
    / "metadata"
    / "comunes_data.geojson"
)

gdf = gpd.read_file(comune_geodata_path)

# add nuts3 code to extinct localities
gdf.loc[gdf.terr_key.isin(["I167", "I252"]), "com_nuts3"] = "ITC42"
gdf["island_comune"] = False
gdf.loc[gdf.terr_key.isin(['B685', 'E348', 'G871', 'L742', 'H072', 'E363', 'D518', 'E431',
       'E606', 'G315', 'L519', 'B789']), "island_comune"] = True

gdf["comune_clean"] = gdf.name_it.normalize_string()

with open(config_path.resolve(), "r", encoding="utf-8") as in_file:
    try:
        config = yaml.safe_load(in_file)
    except yaml.YAMLError as exc:
        print(exc)

long_dfs = []

for file_path in files_to_parse:
    print(f"Parsing file: {file_path.name}")

    pattern = r"^(\d{8})__"
    match = re.search(pattern, file_path.name)
    if match:
        date_str = match.group(1)
    else:
        raise ValueError(f"No date found in filename: {file_path}")

    # print(f"{date_str=}")
    if date_str in [
        "19960421",
        "19990613",
        "20010513",
        "20080413",
        "20090607",
        "20130224",
        "20140525",
        "20220925",
    ]:
        df = pd.read_csv(
            file_path,
            sep=";",
        )
    elif date_str in [
        "20040612",
        "20060409",
        "20180304",
        "20190526",
        "20240609",
    ]:
        df = pd.read_csv(
            file_path,
            sep=";",
            encoding="cp1252",
        )
    else:
        raise ValueError(f"Unrecognised date {date_str}")

    if date_str in ["20010513"]:
        # special treatment of 'comunes' which are parts of comunes
        mask = df["COMUNE"].str.contains(" - ", na=False)
        df.loc[mask, "COMUNE"] = df.loc[mask, "COMUNE"].str.partition(" - ")[0]

        df["COMUNE"] = df["COMUNE"].replace(
            {
                "Roma centro": "Roma",
                "Verona Est": "Verona",
                "Messina centro storico": "Messina",
                "Perugia centro": "Perugia",
                "Foggia centro": "Foggia",
                "Verona Ovest": "Verona",
                "Trieste centro": "Trieste",
            }
        )

    if "vaosta" in str(file_path.name).lower():
        continue

    if date_str in ["20140525", "20180304", "20190526", "20220925"]:
        # special treatment of 'comunes' which are named bilingually
        mask = df["COMUNE"].str.contains("/", na=False)
        df.loc[mask, "COMUNE"] = df.loc[mask, "COMUNE"].str.partition("/")[0]

    if date_str in ["20240609"]:
        # special treatment of 'comunes' which are named bilingually
        mask = df["DESCCOMUNE"].str.contains("/", na=False)
        df.loc[mask, "DESCCOMUNE"] = df.loc[mask, "DESCCOMUNE"].str.partition("/")[0]

    columns = df.columns

    for c in columns:
        is_target = False
        target_name = ""
        for key, targets in config["column_names"].items():
            if c in targets:
                is_target = True
                target_name = key
                df = df.rename(columns={c: target_name})

        print(
            f"{'+' if is_target else ' '} {c[:20].ljust(20) + ('...' if len(c) > 20 else '   ')} -> {target_name}"
        )

    df["comune_clean"] = df["comune"].normalize_string()

    possible_group_cols = [
        "provincia",
        "circoscrizione",
        "regione",
        "collegio",
        "collegio_plurinominale",
        "collegio_uninominale",
    ]

    for c in possible_group_cols:
        if c not in df.columns:
            df[c] = pd.NA

    columns_standard = [
        "comune_clean",
        "collegio_uninominale",
        "collegio_plurinominale",
        "circoscrizione",
        "comune",
        "provincia",
        "regione",
        "eligible_voters",
        "issued_ballots",
        "list_name",
        "votes",
    ]
    columns_locality = [
        "comune_clean",
        "collegio_uninominale",
        "collegio_plurinominale",
        "circoscrizione",
        "comune",
        "provincia",
        "regione",
        "issued_ballots",
        "eligible_voters",
    ]
    df = df[columns_standard]

    assert (
        len(set(df["list_name"]) - set(config["choices_names"].keys())) == 0
    )  # no missing keys

    df["list_name"] = df["list_name"].map(config["choices_names"])

    df_light = (
        df[columns_locality]
        .groupby(columns_locality, dropna=False)
        .first()
        .reset_index()
    )

    merged = gdf.merge(
        right=df_light,
        on="comune_clean",
        how="inner",
    )

    group_cols = [
        "collegio_uninominale",
        "collegio_plurinominale",
        "circoscrizione",
        "provincia",
        "regione",
    ]

    import numpy as np

    merged = merged.to_crs("EPSG:3035")
    merged["mistake"] = False

    for key, group in merged.groupby(group_cols, dropna=False):
        # print(key)
        if len(group) == 1:
            merged.loc[group.index, "mistake"] = True
            continue

        # Find geometries within 1 km of each other
        joined = gpd.sjoin(
            group[["geometry"]],
            group[["geometry"]],
            predicate="dwithin",
            distance=1000,
            how="left",
        )

        # Remove self-matches
        joined = joined[joined.index != joined["index_right"]]

        # Rows with no other geometry within 1 km are mistakes
        has_neighbour = (
            joined.groupby(joined.index).size().reindex(group.index, fill_value=0) > 0
        )

        merged.loc[group.index, "mistake"] = ~has_neighbour

    # remove false positives
    merged.loc[merged['island_comune'], "mistake"] = False

    fig, ax = plt.subplots()

    for _, row in merged[merged.mistake].iterrows():
        annotation_point = row.geometry.representative_point()
        ax.annotate(
            "x",
            xy=(annotation_point.x, annotation_point.y),
            ha="center",
            va="center",
            fontsize=5,
        )

    merged[merged.mistake].plot(ax=ax, color="red")
    merged = merged[~merged.mistake]

    colors = cycle(colormaps["tab20"].colors)
    merged = merged.to_crs("EPSG:3035")
    merged["y"] = merged.centroid.y
    merged.sort_values(by="y")
    for key, group in merged.groupby(group_cols, dropna=False):
        gdf_rep = group.groupby("comune").first()
        color = next(colors)
        gdf_rep.plot(ax=ax, color=color)

    plt.show()
    # raise NotImplementedError

    df_light_unmatched = (
        df_light.merge(
            merged[columns_locality].drop_duplicates(),
            on=columns_locality,
            how="left",
            indicator=True,
        )
        .query("_merge == 'left_only'")
        .drop(columns="_merge")
    )
    # print(df_light_unmatched[columns_locality].T)
    print(f'unmatched count: {len(df_light_unmatched)} / {len(df_light)} = {100 * len(df_light_unmatched) / len(df_light):.2f}')

    

    raise NotImplementedError
