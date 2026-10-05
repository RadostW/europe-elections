# Read README.md in ../data/italy to understand the data better

import yaml
import pandas as pd
import geopandas as gpd
import re
import unidecode


@pd.api.extensions.register_series_accessor("normalize_string")
class NormalizeStringAccessor:
    def __init__(self, s):
        self._obj = s

    def __call__(self):
        return (
            self._obj.astype(str)
            .map(unidecode.unidecode)
            .str.lower()
            .str.replace(r"[^a-z ']", "", regex=True)
            .str.replace(r"['/]", " ",regex=True)
            .str.replace("  ", " ")
            .str.strip()
        )


def load_reference_gdf(gdf_path, date_str):
    gdf = gpd.read_file(gdf_path)

    # add nuts3 code to extinct localities
    gdf.loc[gdf.terr_key.isin(["I167", "I252"]), "com_nuts3"] = "ITC42"
    gdf.loc[gdf.terr_key.isin(["L742"]), "com_nuts3"] = "ITI44"

    # update old codes
    gdf.loc[gdf["com_nuts3"] == "ITD20","com_nuts3"] = "ITH20"
    gdf.loc[gdf["com_nuts3"] == "ITD42","com_nuts3"] = "ITH42"

    gdf["island_comune"] = False
    gdf.loc[
        gdf.terr_key.isin(
            [
                "B685",
                "E348",
                "G871",
                "L742",
                "H072",
                "E363",
                "D518",
                "E431",
                "E606",
                "G315",
                "L519",
                "B789",
                "H803",  # exclave - almost island
            ]
        ),
        "island_comune",
    ] = True

    gdf["comune_clean"] = gdf.name_it.normalize_string()
    gdf["comune_provincia_clean"] = gdf.name_it.normalize_string() + " ( " + gdf.prov_name.normalize_string() + " )"
    gdf.loc[gdf.valid_to.isna(), "valid_to"] = pd.to_datetime("2026-10-05")

    election_datetime = pd.to_datetime(date_str)
    if election_datetime < gdf.valid_from.min():
        election_datetime_clip = gdf.valid_from.min()
    else:
        election_datetime_clip = election_datetime

    gdf_date = gdf[
        (gdf["valid_from"] <= election_datetime_clip)
        & (election_datetime_clip <= gdf["valid_to"])
    ]

    gdf_date_lax = gdf[
        (gdf["valid_from"] - pd.Timedelta(days=1.5 * 365) <= election_datetime_clip)
        & (election_datetime_clip <= gdf["valid_to"] + pd.Timedelta(days=1.5 * 365))
    ]

    return {
        "geodataframe_at_date": gdf_date,
        "geodataframe_at_fuzzy_date": gdf_date_lax,
    }


def load_config(config_path):
    with open(config_path.resolve(), "r", encoding="utf-8") as in_file:
        try:
            config = yaml.safe_load(in_file)
        except yaml.YAMLError as exc:
            print(exc)

    return config


def load_election(election_path):

    pattern = r"^(\d{8})__"
    match = re.search(pattern, election_path.name)
    if match:
        date_str = match.group(1)
    else:
        raise ValueError(f"No date found in filename: {election_path}")

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
            election_path,
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
            election_path,
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

    if "vaosta" in str(election_path.name).lower():
        raise NotImplementedError("vaosta elections not supported for now")

    if date_str in ["20140525", "20180304", "20190526", "20220925"]:
        # special treatment of 'comunes' which are named bilingually
        mask = df["COMUNE"].str.contains("/", na=False)
        df.loc[mask, "COMUNE"] = df.loc[mask, "COMUNE"].str.partition("/")[0]

    if date_str in ["20240609"]:
        # special treatment of 'comunes' which are named bilingually
        mask = df["DESCCOMUNE"].str.contains("/", na=False)
        df.loc[mask, "DESCCOMUNE"] = df.loc[mask, "DESCCOMUNE"].str.partition("/")[0]

    return df
