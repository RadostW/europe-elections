import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import pathlib

here = pathlib.Path(__file__).resolve().parent

# --- CONFIG FILES WITH FOLDER PATH ---
files = {
    "germany": {
        "csv": "../data/downloads/germany.csv",
        "topo": "../data/downloads/germany_kreisen.topojson",
    },
    "poland": {
        "csv": "../data/downloads/poland.csv",
        "topo": "../data/downloads/poland_powiaty.topojson",
    },
    "france": {
        "csv": "../data/downloads/france.csv",
        "topo": "../data/downloads/france_departement.topojson",
    },
    "italy": {
        "csv": "../data/downloads/italy.csv",
        "topo": "../data/downloads/italy_province.topojson",
    },
    "spain": {
        "csv": "../data/downloads/spain.csv",
        "topo": "../data/downloads/spain_provincia.topojson",
    },
    "romania": {
        "csv": "../data/downloads/romania.csv",
        "topo": "../data/downloads/romania_judete.topojson",
    },
    "hungary": {
        "csv": "../data/downloads/hungary.csv",
        "topo": "../data/downloads/hungary_telepules.topojson",
    },
}

gdfs = []

for country, paths in files.items():
    # Load CSV
    df = pd.read_csv(here / paths["csv"])

    # Filter only European elections
    df = df[df["election_type"] == "european"]

    # Last European election date
    last_date = df["election_date"].max()
    df_last = df[df["election_date"] == last_date]

    # Extract eligible voters and issued ballots
    votes_df = df_last[
        df_last["type"].isin([0, 1])
    ]  # 0=eligible_voters, 1=issued_ballots
    pivot = votes_df.pivot(index="harmonised_code", columns="type", values="votes")
    pivot.columns = ["eligible_voters", "issued_ballots"]
    pivot["turnout"] = pivot["issued_ballots"] / pivot["eligible_voters"]
    pivot.reset_index(inplace=True)

    # Load TopoJSON
    gdf = gpd.read_file(here / paths["topo"])

    # Merge with turnout data using correct key
    gdf = gdf.merge(
        pivot, left_on="harmonised_code", right_on="harmonised_code", how="outer"
    )

    gdf["country"] = country
    gdfs.append(gdf.copy())

# Combine Germany and Poland
gdf_all = pd.concat(gdfs, ignore_index=True)


# Set CRS if missing (assume WGS84)
if gdf_all.crs is None:
    gdf_all = gdf_all.set_crs(epsg=4326)

# --- REPROJECT TO EUROPEAN STANDARD (EPSG:3035) ---
gdf_all = gdf_all.to_crs("EPSG:4326")

# --- PLOT MAP ---
fig, ax = plt.subplots(1, 1, figsize=(14, 12))
gdf_all["turnout_clip"] = gdf_all["turnout"].clip(0.25, 0.75)
gdf_all.plot(
    column="turnout_clip",
    ax=ax,
    cmap="cividis",
    legend=False,  # no color bar
    missing_kwds={"color": "red"},
    edgecolor="black",
    linewidth=0.2,
)

ax.axis("off")
ax.set_ylim([35, 56])
ax.set_xlim([-10, None])
plt.tight_layout()

plt.savefig("banner.png", dpi=100, bbox_inches="tight", transparent=True)

plt.show()
