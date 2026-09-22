import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import pathlib

here = pathlib.Path(__file__).resolve().parent

STYLE_FILE = here / "elections.mplstyle"
plt.style.use(STYLE_FILE)
plt.rcParams.update({"lines.marker": ""})  # no default markers


# --- CONFIG FILES WITH FOLDER PATH ---
files = {
    "germany": {
        "csv": "../data/downloads/germany_best_resolution.csv",
        "topo": "../data/downloads/best_resolution_maps/germany_kreisen.topojson",
    },
    "poland": {
        "csv": "../data/downloads/poland_best_resolution.csv",
        "topo": "../data/downloads/best_resolution_maps/poland_powiaty.topojson",
    },
    "france": {
        "csv": "../data/downloads/france_best_resolution.csv",
        "topo": "../data/downloads/best_resolution_maps/france_departement.topojson",
    },
    "italy": {
        "csv": "../data/downloads/italy_best_resolution.csv",
        "topo": "../data/downloads/best_resolution_maps/italy_province.topojson",
    },
    "spain": {
        "csv": "../data/downloads/spain_best_resolution.csv",
        "topo": "../data/downloads/best_resolution_maps/spain_provincia.topojson",
    },
    "romania": {
        "csv": "../data/downloads/romania_best_resolution.csv",
        "topo": "../data/downloads/best_resolution_maps/romania_judete.topojson",
    },
    "hungary": {
        "csv": "../data/downloads/hungary_best_resolution.csv",
        "topo": "../data/downloads/best_resolution_maps/hungary_telepules.topojson",
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
    pivot = votes_df.pivot(index=["harmonised_code","harmonised_name"], columns="type", values="votes")
    pivot.columns = ["eligible_voters", "issued_ballots"]
    pivot["turnout"] = pivot["issued_ballots"] / pivot["eligible_voters"]
    pivot.reset_index(inplace=True)

    # Load TopoJSON
    gdf = gpd.read_file(here / paths["topo"])

    # Merge with turnout data using correct key
    gdf = gdf.merge(
        pivot, left_on="harmonised_code", right_on="harmonised_code", how="outer"
    )

    # drop French remote islands for plots
    gdf = gdf[
        ~gdf[f"harmonised_code"].str.startswith("M_97")
    ]
    gdf = gdf[
            ~gdf[f"harmonised_code"].str.startswith("M_98")
        ]

    # drop Spanish remote islands for plots
    gdf = gdf[
                ~gdf[f"harmonised_code"].str.startswith("I_38")
            ]
    gdf = gdf[
                    ~gdf[f"harmonised_code"].str.startswith("I_35")
                ]

    gdf["country"] = country
    gdfs.append(gdf.copy())

# Combine Germany and Poland
gdf_all = pd.concat(gdfs, ignore_index=True)


# Set CRS if missing (assume WGS84)
if gdf_all.crs is None:
    gdf_all = gdf_all.set_crs(epsg=4326)

# --- REPROJECT TO EUROPEAN STANDARD (EPSG:3035) ---
gdf_all = gdf_all.to_crs("EPSG:3035")

# --- PLOT MAP ---

FIG_WIDTH, FIG_HEIGHT = (3.5, 2.5)
fig, ax = plt.subplots(
    1,
    1,
    figsize=(FIG_WIDTH, FIG_HEIGHT),
    constrained_layout=True,
)

# fig, ax = plt.subplots(1, 1, figsize=(14, 12))
# gdf_all["turnout_clip"] = gdf_all["turnout"].clip(0.25, 0.75)
gdf_all["turnout_clip"] = gdf_all["turnout"].clip(0.2, 0.8)
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
# ax.set_ylim([35, 56])
# ax.set_xlim([-10, None])
ax.set_title(f"European election turnout", fontsize=9)
# plt.tight_layout()

plt.savefig(
    "ep_turnout_best_resolution.png", dpi=300, bbox_inches="tight", transparent=True
)
# plt.savefig(
#     "ep_turnout_best_resolution.pdf", dpi=300, bbox_inches="tight", transparent=True
# )

plt.show()
