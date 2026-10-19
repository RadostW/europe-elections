import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import pathlib

here = pathlib.Path(__file__).resolve().parent
countries = ["germany", "poland", "france", "italy", "spain", "romania", "hungary"]
downloads_dir = here / ".." / "data" / "downloads"

graphics_dir = here / ".." / "data" / "graphics"

STYLE_FILE = here / "elections.mplstyle"
plt.style.use(STYLE_FILE)
plt.rcParams.update({"lines.marker": ""})  # no default markers

FIGURE_WIDTH = 6
FIGURE_HEIGHT = 5
fig, axes = plt.subplots(
    2,
    2,
    figsize=(FIGURE_WIDTH, FIGURE_HEIGHT),
    constrained_layout=True,
    sharex=True,
    sharey=True,
)

tile_name = {
    "france": "departement",
    "germany": "kreisen",
    "hungary": "telepules",
    "italy": "comune",
    "poland": "powiaty",
    "romania": "judete",
    "spain": "provincia",
}

for nuts_level in [4, 3, 2, 1]:

    ax = axes.flatten()[nuts_level - 1]

    for country in countries:
        # Load CSV
        if nuts_level in [1, 2, 3]:
            df = pd.read_csv(downloads_dir / f"{country}_nuts_{nuts_level}.csv")
            code_column = f"nuts_{nuts_level}_code"
            name_column = f"nuts_{nuts_level}_name"
        elif nuts_level == 4:
            df = pd.read_csv(downloads_dir / f"{country}_best_resolution.csv")
            code_column = f"harmonised_code"
            name_column = f"harmonised_name"
        else:
            raise ValueError

        # Filter only European elections
        df = df[df["election_type"] == "european"]

        # Last European election date
        last_date = df["election_date"].max()
        df_last = df[df["election_date"] == last_date]

        # Extract eligible voters and issued ballots
        last_euro_df = df_last[
            df_last["type"].isin([0, 1])
        ]  # 0=eligible_voters, 1=issued_ballots
        turnout_df = last_euro_df.pivot(
            index=[code_column, name_column],
            columns="name",
            values="votes",
        )
        # pivot.columns = ["eligible_voters", "issued_ballots"]
        turnout_df["turnout"] = (
            turnout_df["issued_ballots"] / turnout_df["eligible_voters"]
        )
        turnout_df = turnout_df.reset_index()

        if nuts_level in [1, 2, 3]:
            gdf = gpd.read_file(downloads_dir / f"{country}_nuts_{nuts_level}.topojson")
        elif nuts_level == 4:
            gdf = gpd.read_file(
                downloads_dir
                / "best_resolution_maps"
                / f"{country}_{tile_name[country]}.topojson"
            )
        else:
            raise ValueError

        turnout_gdf = gdf.merge(turnout_df, on=[code_column])

        if turnout_gdf.crs is None:
            turnout_gdf = turnout_gdf.set_crs(epsg=4326)

        # --- REPROJECT TO EUROPEAN STANDARD (EPSG:3035) ---
        turnout_gdf = turnout_gdf.to_crs("EPSG:3035")

        turnout_gdf["turnout_clip"] = turnout_gdf["turnout"].clip(0.2, 0.8)

        # drop French remote islands for plots

        if nuts_level in [1, 2, 3]:

            turnout_gdf = turnout_gdf[
                ~turnout_gdf[f"nuts_{nuts_level}_code"].str.startswith("FRY")
            ]

            # drop Spanish remote islands for plots
            turnout_gdf = turnout_gdf[
                ~turnout_gdf[f"nuts_{nuts_level}_code"].str.startswith("ES7")
            ]

        turnout_gdf.plot(
            column="turnout_clip",
            ax=ax,
            cmap="cividis",
            legend=False,  # no color bar
            missing_kwds={"color": "red"},
            edgecolor="#888",
            linewidth=0.1,
            vmin=0.2,
            vmax=0.8,
            rasterized=(nuts_level == 4),
        )

    ax.axis("off")
    ax.set_xlim(2605935.6236845357, 6008581.445644909)
    ax.set_ylim(1277558.7819906692, 3664873.221989863)

plt.savefig(here / "resolution_comparison.pdf", dpi=600)
plt.show()
