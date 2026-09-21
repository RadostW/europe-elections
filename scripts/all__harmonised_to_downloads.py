import pandas as pd
import geopandas as gpd
import topojson
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

OUTPUT_DIR = HERE / ".." / "data" / "downloads"

countries = {
    "germany": {
        "code": "DE",
        "csv": HERE
        / ".."
        / "data"
        / "germany"
        / "harmonised"
        / "kreisen"
        / "germany__long.csv",
        "meta": {
            "path": HERE
            / ".."
            / "data"
            / "germany"
            / "harmonised"
            / "kreisen"
            / "germany__region_data.csv",
            "harmonised_code_column": "ags",
            "harmonised_name_column": "kreis_name",
            "nuts_3_code_column": "nuts",
        },
    },
    "poland": {
        "code": "PL",
        "csv": HERE
        / ".."
        / "data"
        / "poland"
        / "harmonised"
        / "powiaty"
        / "poland__long.csv",
        "meta": {
            "path": HERE
            / ".."
            / "data"
            / "poland"
            / "harmonised"
            / "powiaty"
            / "poland__region_data.csv",
            "harmonised_code_column": "teryt",
            "harmonised_name_column": "pow_name",
            "nuts_3_code_column": "nuts",
        },
    },
    "spain": {
        "code": "ES",
        "csv": HERE
        / ".."
        / "data"
        / "spain"
        / "harmonised"
        / "provincias"
        / "spain.csv",
        "meta": {
            "path": HERE
            / ".."
            / "data"
            / "spain"
            / "harmonised"
            / "provincias"
            / "spain__region_data.csv",
            "harmonised_code_column": "harmonised_code",
            "harmonised_name_column": "harmonised_name",
            "nuts_3_code_column": "nuts3_code",
        },
    },
    "italy": {
        "code": "IT",
        "csv": HERE / ".." / "data" / "italy" / "harmonised" / "province" / "italy.csv",
    },
    "france": {
        "code": "FR",
        "csv": HERE
        / ".."
        / "data"
        / "france"
        / "harmonised"
        / "departament"
        / "france__long.csv",
        "meta": {
            "path": HERE
            / ".."
            / "data"
            / "france"
            / "harmonised"
            / "departament"
            / "france__region_data.csv",
            "harmonised_code_column": "harmonised_code",
            "harmonised_name_column": "harmonised_name",
            "nuts_3_code_column": "nuts",
        },
    },
    "romania": {
        "code": "RO",
        "csv": HERE
        / ".."
        / "data"
        / "romania"
        / "harmonised"
        / "judete"
        / "romania__long.csv",
    },
    "hungary": {
        "code": "HU",
        "csv": HERE / ".." / "data" / "hungary" / "harmonised" / "hungary.csv",
        "meta": {
            "path": HERE
            / ".."
            / "data"
            / "hungary"
            / "harmonised"
            / "hungary__region_data.csv",
            "harmonised_code_column": "harmonised_code",
            "harmonised_name_column": "harmonised_name",
            "nuts_3_code_column": "nuts3_code",
        },
    },
}

NUTS_TOPO_PATH = (
    HERE / ".." / "data" / "all" / "metadata" / "NUTS_RG_01M_2024_4326.topojson"
)

full_gdf = gpd.read_file(NUTS_TOPO_PATH)

fusions = {
    "ES53X": {
        "oldids": ["ES531", "ES532", "ES533"],
        "newname": "Illes Balears",
    },
    "ES70X": {
        "oldids": ["ES703", "ES706", "ES707", "ES708", "ES709"],
        "newname": "Canarias A",
    },
    "ES70Y": {
        "oldids": ["ES704", "ES705"],
        "newname": "Canarias B",
    },
}

artificial_regions = []
for newid, fusion_desc in fusions.items():

    oldids = fusion_desc["oldids"]
    newname = fusion_desc["newname"]

    # Get geometries to fuse
    geometries = full_gdf.loc[full_gdf["NUTS_ID"].isin(oldids), "geometry"]

    if len(geometries) != len(oldids):
        missing = set(oldids) - set(full_gdf["NUTS_ID"])
        raise ValueError(f"{newid}: missing NUTS IDs: {missing}")

    # Fuse geometries
    fused_geometry = geometries.union_all()

    # Create new record
    artificial_regions.append(
        {
            "id": newid,
            "NUTS_ID": newid,
            "LEVL_CODE": 3,
            "CNTR_CODE": newid[:2],
            "NAME_LATN": newname,
            "NUTS_NAME": newname,
            # "MOUNT_TYPE": pd.NA,
            # "URBN_TYPE": pd.NA,
            # "COAST_TYPE": pd.NA,
            "geometry": fused_geometry,
        }
    )

# Add all new regions at once
artificial_regions = gpd.GeoDataFrame(
    artificial_regions,
    crs=full_gdf.crs,
)

full_gdf = pd.concat(
    [full_gdf, artificial_regions],
    ignore_index=True,
)

# Construct table of nuts correspondences
nuts_3_table = full_gdf[full_gdf["LEVL_CODE"] == 3][["NAME_LATN", "NUTS_ID"]].rename(
    columns={
        "NAME_LATN": "nuts_3_name",
        "NUTS_ID": "nuts_3_code",
    }
)
nuts_2_table = full_gdf[full_gdf["LEVL_CODE"] == 2][["NAME_LATN", "NUTS_ID"]].rename(
    columns={
        "NAME_LATN": "nuts_2_name",
        "NUTS_ID": "nuts_2_code",
    }
)
nuts_1_table = full_gdf[full_gdf["LEVL_CODE"] == 1][["NAME_LATN", "NUTS_ID"]].rename(
    columns={
        "NAME_LATN": "nuts_1_name",
        "NUTS_ID": "nuts_1_code",
    }
)

nuts_3_table["nuts_2_code"] = nuts_3_table["nuts_3_code"].str[:4]
nuts_3_table["nuts_1_code"] = nuts_3_table["nuts_3_code"].str[:3]

nuts_table = pd.merge(
    nuts_1_table,
    pd.merge(nuts_2_table, nuts_3_table, on="nuts_2_code"),
    on="nuts_1_code",
)

# Set CRS if missing (assume WGS84)
if full_gdf.crs is None:
    full_gdf = full_gdf.set_crs(epsg=4326)

for country, country_desc in countries.items():
    country_code = country_desc["code"]

    # load election data and merge with nuts
    election_df = pd.read_csv(country_desc["csv"])

    if "meta" in country_desc.keys():
        meta_df = pd.read_csv(country_desc["meta"]["path"])
        meta_df["nuts_3_code"] = meta_df[country_desc["meta"]["nuts_3_code_column"]]
        meta_df["harmonised_code"] = meta_df[
            country_desc["meta"]["harmonised_code_column"]
        ]
        meta_df["harmonised_name"] = meta_df[
                    country_desc["meta"]["harmonised_name_column"]
                ]

        smr = meta_df["harmonised_code"].value_counts().reset_index()
        if len(smr[smr["count"] > 1]):
            print("[WARN] Encountered duplicated harmonised codes in translation table")
            dups = set(smr[smr["count"] > 1]["harmonised_code"])
            print(meta_df[meta_df["harmonised_code"].isin(dups)])

        election_df = pd.merge(
            left=election_df,
            right=meta_df[["harmonised_code", "nuts_3_code"]],
            how="left",
            on="harmonised_code",
        )

        if len(election_df[election_df.nuts_3_code.isna()]) > 0:
            print("[WARN] Encountered unknown codes (missing from meta table)")
            diag = str(
                election_df[election_df.nuts_3_code.isna()][
                    ["harmonised_name", "harmonised_code"]
                ].value_counts()
            ).split("\n")
            for line in diag:
                print("[WARN] " + line)
    else:
        election_df["nuts_3_code"] = election_df["harmonised_code"]

    known_codes = set(
        nuts_table[nuts_table["nuts_3_code"].str.startswith(country_code)][
            "nuts_3_code"
        ]
    )
    if (
        len(
            election_df[
                (~election_df.nuts_3_code.isin(known_codes))
                & election_df.nuts_3_code.notna()
            ]
        )
        > 0
    ):
        print("[WARN] Encountered unknown codes (missing from nuts table)")
        diag = str(
            election_df[~election_df.nuts_3_code.isin(known_codes)][
                ["harmonised_name", "harmonised_code", "nuts_3_code"]
            ].value_counts()
        ).split("\n")
        for line in diag:
            print("[WARN] " + line)

    nuts_3_codes_missing = known_codes - set(election_df["nuts_3_code"])
    fused_ids = set(sum([f["oldids"] for f in fusions.values()], start=[]))
    missing_but_not_fused = nuts_3_codes_missing - fused_ids
    if len(missing_but_not_fused) > 0:
        print("[WARN] NUTS 3 codes missing")
        print("[WARN] " + str(nuts_3_codes_missing))
        print("[WARN]  Missing but not fused")
        print("[WARN]  " + str(nuts_3_codes_missing - fused_ids))

    election_df["nuts_2_code"] = election_df["nuts_3_code"].str[:4]
    election_df["nuts_1_code"] = election_df["nuts_3_code"].str[:3]

    election_df["election_date"] = election_df["election_date"].str.replace("_", "-")

    election_type_names = {
        "bundestag": "parliament",
        "camera": "parliament",
        "congresso": "parliament",
        "european": "european",
        "house": "parliament",
        "parliament": "parliament",
        "president_a": "president_a",
        "president_b": "president_b",
        "sejm": "parliament",
    }

    if len(set(election_df["election_type"]) - set(election_type_names.keys())) > 0:
        raise ValueError("Unknown election type")

    election_df["election_type"] = election_df["election_type"].map(election_type_names)

    for level in [1, 2, 3, 4]:
        if level == 4:  # max resolution
            columns = [
                "election_date",
                "election_type",
                "harmonised_code",
                "harmonised_name",
                "type",
                "name",
                "votes",
            ]
            level_df = election_df[columns].sort_values(by=columns)
        else:
            columns = [
                "election_date",
                "election_type",
                f"nuts_{level}_code",
                f"nuts_{level}_name",
                "type",
                "name",
                "votes",
            ]
            level_df = election_df.merge(
                nuts_table[[f"nuts_{level}_code", f"nuts_{level}_name"]], how="left"
            )
            level_df = level_df[columns].sort_values(by=columns)

        if level == 4:
            elections_filename = f"{country}_best_resolution.csv"
        else:
            elections_filename = f"{country}_nuts_{level}.csv"

        level_aggregated = level_df.groupby(columns[:-1]).sum().reset_index()
        level_aggregated.to_csv(OUTPUT_DIR / elections_filename)

    if "meta" in country_desc.keys():
        region_data = pd.merge(
            meta_df[["harmonised_code", "harmonised_name", "nuts_3_code"]],
            nuts_table,
            on="nuts_3_code",
        )
        region_data = region_data[
            [
                "harmonised_code",
                "harmonised_name",
                "nuts_3_code",
                "nuts_3_name",
                "nuts_2_code",
                "nuts_2_name",
                "nuts_1_code",
                "nuts_1_name",
            ]
        ]
    else:
        present_codes = set(election_df["nuts_3_code"])
        region_data = nuts_table[nuts_table["nuts_3_code"].isin(present_codes)].copy()
        region_data["harmonised_code"] = region_data["nuts_3_code"]
        region_data["harmonised_name"] = region_data["nuts_3_name"]

        region_data = region_data[
            [
                "harmonised_code",
                "harmonised_name",
                "nuts_3_code",
                "nuts_3_name",
                "nuts_2_code",
                "nuts_2_name",
                "nuts_1_code",
                "nuts_1_name",
            ]
        ]

    region_data.to_csv(OUTPUT_DIR / f"{country}_region_metadata.csv")    

    # prepare maps for displaying
    for nuts_level in [3, 2, 1]:
        gdf_country_nuts = full_gdf[
            (full_gdf["CNTR_CODE"] == country_code)
            & (full_gdf["LEVL_CODE"] == nuts_level)
        ].copy()
        gdf_country_nuts = gdf_country_nuts[
            ["NUTS_ID", "NUTS_NAME", "geometry"]
        ].reset_index()
        gdf_country_nuts = gdf_country_nuts.rename(
            columns={
                "NUTS_ID": f"nuts_{nuts_level}_code",
                "NUTS_NAME": f"nuts_{nuts_level}_name",
            }
        )

        print(f"cntry {country}, level {nuts_level}: {len(gdf_country_nuts)}")

        # gdf_ro.to_file(output_geojson, driver="GeoJSON")

        topology = topojson.Topology(gdf_country_nuts, prequantize=1e3)
        topology.to_json(OUTPUT_DIR / f"{country}_nuts_{nuts_level}.topojson")

        gdf_country_nuts.to_file(
            OUTPUT_DIR / f"{country}_nuts_{nuts_level}.geojson", driver="GeoJSON"
        )
