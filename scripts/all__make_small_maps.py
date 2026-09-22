import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import pathlib

here = pathlib.Path(__file__).resolve().parent
countries = ["germany", "poland", "france", "italy", "spain", "romania", "hungary"]
# countries = ["germany"]
downloads_dir = here / ".." / "data" / "downloads"

graphics_dir = here / ".." / "data" / "graphics"

STYLE_FILE = here / "elections.mplstyle"
plt.style.use(STYLE_FILE)
plt.rcParams.update({"lines.marker": ""})  # no default markers

for nuts_level in [3, 2, 1]:

    FIG_WIDTH, FIG_HEIGHT = (3.5, 2.5)
    fig, ax = plt.subplots(
        1,
        1,
        figsize=(FIG_WIDTH, FIG_HEIGHT),
        constrained_layout=True,
    )

    for country in countries:
        # Load CSV
        df = pd.read_csv(downloads_dir / f"{country}_nuts_{nuts_level}.csv")

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
            index=[f"nuts_{nuts_level}_code", f"nuts_{nuts_level}_name"],
            columns="name",
            values="votes",
        )
        # pivot.columns = ["eligible_voters", "issued_ballots"]
        turnout_df["turnout"] = (
            turnout_df["issued_ballots"] / turnout_df["eligible_voters"]
        )
        turnout_df = turnout_df.reset_index()

        # Load TopoJSON
        gdf = gpd.read_file(downloads_dir / f"{country}_nuts_{nuts_level}.topojson")
        turnout_gdf = gdf.merge(
            turnout_df, on=[f"nuts_{nuts_level}_code", f"nuts_{nuts_level}_name"]
        )

        if turnout_gdf.crs is None:
            turnout_gdf = turnout_gdf.set_crs(epsg=4326)

        # --- REPROJECT TO EUROPEAN STANDARD (EPSG:3035) ---
        turnout_gdf = turnout_gdf.to_crs("EPSG:3035")

        turnout_gdf["turnout_clip"] = turnout_gdf["turnout"].clip(0.2, 0.8)

        # drop French remote islands for plots
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
            edgecolor="black",
            linewidth=0.2,
            vmin=0.2,
            vmax=0.8,
        )

    ax.axis("off")
    ax.set_title(f"European election turnout (NUTS {nuts_level})", fontsize=9)

    plt.savefig(
        graphics_dir / f"ep_turnout_nuts_{nuts_level}.png",
        dpi=300,
        bbox_inches="tight",
        transparent=True,
    )
    # plt.savefig(
    #     graphics_dir / f"ep_turnout_nuts_{nuts_level}.pdf",
    #     dpi=300,
    #     bbox_inches="tight",
    #     transparent=True,
    # )
