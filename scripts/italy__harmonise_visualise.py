import matplotlib.pyplot as plt

from itertools import cycle
from matplotlib import colormaps

def visualise(
    matched_mistakes,
    matched_gdf,
    columns_neighbourhood
):
    fig, ax = plt.subplots()

    for _, row in matched_gdf.iterrows():
        if row['match_method'] == 'fuzzy':
            annotation_point = row.geometry.representative_point()
            ax.annotate(
                "x",
                xy=(annotation_point.x, annotation_point.y),
                ha="center",
                va="center",
                fontsize=5,
            )
        if row['match_method'] == 'very_fuzzy':
            annotation_point = row.geometry.representative_point()
            ax.annotate(
                "o",
                xy=(annotation_point.x, annotation_point.y),
                ha="center",
                va="center",
                fontsize=5,
            )            

    matched_mistakes.plot(ax=ax, color="red")

    colors = cycle(colormaps["tab20"].colors)
    matched_gdf["y"] = matched_gdf.representative_point().y
    matched_gdf["x"] = matched_gdf.representative_point().x
    matched_gdf = matched_gdf.sort_values(by="com_nuts3")
    # for key, group in matched_gdf.groupby(columns_neighbourhood, dropna=False):
    for key, group in matched_gdf.groupby("com_nuts3", dropna=False):
        gdf_rep = group.groupby("comune").first()
        color = next(colors)
        gdf_rep.plot(ax=ax, color=color)

    plt.show()