import geopandas as gpd
import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd
from glob import glob

# Set this to the directory where your shapefile components are located
raw_dir = os.path.join(os.path.dirname(__file__), "../../data/poland/raw_datasets")
harmonised_dir = os.path.join(
    os.path.dirname(__file__), "../../data/poland/harmonised_datasets"
)
graphics_dir = os.path.join(os.path.dirname(__file__), "../../data/poland/graphics")

shapefile_name = "nuts3_poland.geojson"
shapefile_path = os.path.join(raw_dir, shapefile_name)

# Load the shapefile
gdf = gpd.read_file(shapefile_path)
poland_nuts3 = gdf[gdf["NUTS_ID"].str.match(r"PL[0-9A-Z]{3}")]
poland_nuts3 = poland_nuts3.to_crs(epsg=2180)

file_pattern = os.path.join(harmonised_dir, "poland__president*.csv")
csv_files = glob(file_pattern)

if not csv_files:
    raise ValueError("No files found")


def make_plot(gdf, df, column, reference, standard_name, vmin, vmax):

    fig, ax = plt.subplots(figsize=(10, 10))
    merged = gdf.merge(df, left_on="NUTS_ID", right_on="nuts_3_code")
    merged["value"] = merged[column] / merged[reference]
    choropleth = merged.plot(
        column="value",
        cmap="viridis",
        edgecolor="black",
        linewidth=0.5,
        ax=ax,
        vmin=vmin,
        vmax=vmax,
    )

    sm = choropleth.collections[0]
    cax = ax.inset_axes((1.05, 0, 0.03, 1.0))

    plt.colorbar(sm, cax=cax)

    ax.set_frame_on(False)
    ax.set_xticks([])
    ax.set_yticks([])

    fig.tight_layout()

    graphics_path = os.path.join(graphics_dir, f"{standard_name}_{column}.pdf")
    plt.savefig(graphics_path)
    plt.close(fig)


for file_path in sorted(csv_files):
    standard_name = os.path.basename(file_path)[: len("poland__president_2000_a")]
    output_path = os.path.join(harmonised_dir, f"{standard_name}.csv")

    election_df = pd.read_csv(file_path)

    numeric_cols = election_df.select_dtypes(include="number").columns.tolist()
    numeric_cols.remove("eligible_voters")

    make_plot(
        poland_nuts3, election_df, "issued_ballots", "eligible_voters", standard_name, vmin=0.0, vmax=0.7
    )
