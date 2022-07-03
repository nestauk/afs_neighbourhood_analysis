import altair as alt
import geopandas as gp
import json
import numpy as np
import pandas as pd
import requests
from scipy.stats import ttest_ind
from toolz import pipe

from afs_neighbourhood_analysis import PROJECT_DIR

# %%

shape_path = f"{PROJECT_DIR}/inputs/c_au_boundaries.json"


# %%
def fetch_geojson(url: str) -> pd.DataFrame:
    """Fetch a geojson from the open geography portal."""

    return pipe(
        requests.get(url),
        lambda req: [e["properties"] for e in req.json()["features"]],
        pd.DataFrame,
    )


def make_code_name_lookup() -> dict:
    """Create a lookup between geography codes and names.
    We need to stitch this from different sources"""

    county_json = pipe(
        fetch_geojson(
            "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/CTY_APR_2019_EN_NC/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
        ),
        lambda df: df.set_index("CTY19CD")["CTY19NM"].to_dict(),
    )

    lad_json = (
        pd.read_excel(
            "https://www.arcgis.com/sharing/rest/content/items/c4f647d8a4a648d7b4a1ebf057f8aaa3/data"
        )
        .set_index(["LAD21CD"])["LAD21NM"]
        .to_dict()
    )

    unitary_2021 = pipe(
        fetch_geojson(
            "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Counties_and_Unitary_Authorities_December_2021_UK_BGC/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
        ),
        lambda df: df.set_index("CTYUA21CD")["CTYUA21NM"].to_dict(),
    )

    return {**county_json, **lad_json, **unitary_2021}


def get_code_nuts_lookup() -> dict:
    """Lookup between geo codes and NUTS region."""

    lad_nuts = (
        pd.read_excel(
            "https://www.arcgis.com/sharing/rest/content/items/c110087ae04a4cacb4ab0aef960936ce/data"
        )
        .set_index("LAD20CD")["ITL121NM"]
        .to_dict()
    )

    lad_county = pipe(
        fetch_geojson(
            "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LAD21_CTY21_EN_LU/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"
        ),
        lambda df: df.set_index("LAD21CD")["CTY21CD"],
    )

    return {
        **{code: name for code, name in lad_nuts.items()},
        **{lad_county[lad]: lad_nuts[lad] for lad in set(lad_county.keys())},
    }


def plot_ey_perf(ey_results: pd.DataFrame, year: int, gender: str) -> alt.Chart:
    """Boxplot comparing early year performance in different clusters
    Args:
        ey: early years dataframe (includes cluster label)
        year: year we want to focus on
        gender: gender we want to focus on ("Boys", "Girls" or "Total)
    """

    return (
        alt.Chart(ey_results.query(f"year=={year}").query(f"gender=='{gender}'"))
        .mark_boxplot()
        .encode(
            y=alt.Y("cluster:O", title="Cluster"),
            color=alt.Color("cluster:N", title="Cluster"),
            x=alt.X("zscore", title="Z-score"),
            tooltip=["la_name"],
            column=alt.Column("indicator", title="Outcome"),
        )
    ).properties(width=200)


# def plot_ey_trend(ey: pd.DataFrame, gender: str = "Total") -> alt.Chart:
#     """Plot early year trends by """

#     return (
#         alt.Chart(ey.query(f"gender=='{gender}'"))
#         .mark_boxplot()
#         .encode(
#             x="year:O",
#             y="zscore",
#             column="cluster",
#             color="cluster:N",
#             row="indicator",
#             tooltip=["la_name", "cluster"],
#         )
#     ).properties(width=100, height=100)


def plot_ey_year_comp(ey_results: pd.DataFrame, gender="Total") -> alt.Chart:
    """Boxplot comparing early year outcomes by year and cluster
    Args:
        ey_results: early year outcomes (including cluster for an area)
        gender: gender to display
    """

    return (
        alt.Chart(ey_results.query(f"gender=='{gender}'"))
        .mark_boxplot()
        .encode(
            column="year:O",
            y="zscore",
            x="cluster:N",
            color="cluster:N",
            row="indicator",
            tooltip=["la_name", "cluster"],
        )
    ).properties(width=100, height=100)


def plot_ey_evol(ey_results: pd.DataFrame, gender: str):
    """Linechart with the evolution of EY performance by cluster and indicator,
    as well as the median
    Args:
        ey_results: early year outcomes (including cluster for an area)
        gender: gender to display

    """
    # Chart with all areas
    all_areas = (
        alt.Chart()
        .mark_line(point=True)
        .encode(
            x="year:N",
            y=alt.Y("zscore", scale=alt.Scale(zero=False)),
            color="cluster:N",
            detail="la_name",
            tooltip=["la_name", "zscore"],
        )
    ).properties(width=100, height=100)

    # Chart with mean by area
    mean = (
        alt.Chart()
        .mark_line(point=False, color="black")
        .encode(
            x="year:N",
            y=alt.Y("median(zscore)", scale=alt.Scale(zero=False), title="Score"),
        )
    ).properties(width=100, height=100)

    return (
        alt.layer(all_areas, mean, data=ey_results.query(f"gender=='{gender}'"))
        .facet(row="indicator", column="cluster:N")
        .resolve_scale(y="independent")
    )


def phf_for_analysis(
    ph_table: pd.DataFrame, cluster_lookup: dict, code_name_lookup: dict
) -> pd.DataFrame:
    """Prepares the public health frame-work table for analysis
    Args:
        ph_table: public health framework dataset (wide table)
        cluster_lookup: lookup between local authority and cluster
        code_name_lookup: lookup between geography code and name

    """
    return (
        ph_table.stack()
        .reset_index(name="score")
        .assign(cluster=lambda df: df["area_code"].map(cluster_lookup))
        .assign(area_name=lambda df: df["area_code"].map(code_name_lookup))
    )


def calc_mean_ph(ph_long: pd.DataFrame) -> pd.DataFrame:
    """Calculates the mean score in a cluster
    for all public health framework indicators
    """

    # Calculate means
    ph_agg = pd.concat(
        [
            ph_long.rename(columns={"score": name})
            .groupby(["cluster", "indicator_name_expanded"])[name]
            .apply(lambda x: function(x))
            for function, name in zip([np.mean, np.std], ["mean", "std"])
        ],
        axis=1,
    ).reset_index()

    # Add a variable with the rank of each indicator in its mean dispersion
    # e.g. wheter the cluster means are concentrated or dispersed
    return ph_agg.assign(
        rank=lambda df: df["indicator_name_expanded"].map(
            ph_agg.groupby("indicator_name_expanded")["mean"].std().rank(ascending=True)
        )
    )


def phf_ttest(
    phf_long: pd.DataFrame, sig_level: float = 0.05, equal_var: bool = True
) -> pd.DataFrame:
    """For each indicator and cluster, it tests the difference between its mean
    and the rest of the data.
    Args:
        phf_long: public health framework data including cluster
        sig_level: level at which we consider differences significant
        equal_var: whether we assume same or different variance between a
            cluster and the rest of the data
    """

    test_results = []

    for ind in phf_long["indicator_name_expanded"].unique():

        ind_df = phf_long.query(f"indicator_name_expanded == '{ind}'").reset_index(
            drop=True
        )

        for cl in ind_df["cluster"].unique():

            ttest = ttest_ind(
                ind_df.query(f"cluster=={cl}")["score"],
                ind_df.query(f"cluster!={cl}")["score"],
                equal_var=equal_var,
            )

            test_results.append([ind, cl, ttest.pvalue])

    return pd.DataFrame(
        test_results, columns=["indicator", "cluster", "ttest_sign"]
    ).assign(is_sig=lambda df: df["ttest_sign"] < sig_level)


def plot_phf_differences(
    phf_long: pd.DataFrame, sig_level: float = 0.05, equal_var: bool = True
) -> pd.DataFrame:
    """Heatmap of mean scores for each cluster in an indicator.
    We only visualise those that are significantly different from the mean

    Args:
        phf_long: public health framework data including cluster
        sig_level: level at which we consider differences significant
        equal_var: whether we assume same or different variance between a
            cluster and the rest of the data

    """

    return (
        alt.Chart(
            pipe(phf_long, calc_mean_ph)
            .merge(
                phf_ttest(phf_long, sig_level, equal_var),
                left_on=["indicator_name_expanded", "cluster"],
                right_on=["indicator", "cluster"],
            )
            .query("is_sig == True")
        )
        .mark_rect(filled=True)
        .encode(
            x=alt.X(
                "indicator_name_expanded",
                title="Indicator",
                sort=alt.EncodingSortField("rank", order="descending"),
                axis=alt.Axis(labels=False, ticks=False),
            ),
            y=alt.Y("cluster:N", title="Cluster"),
            color=alt.Color(
                "mean", scale=alt.Scale(scheme="Redblue", reverse=True), title="Mean"
            ),
            tooltip=["cluster", "indicator_name_expanded", "mean"],
        )
        .properties(width=800, height=300)
    )


def get_gender_gap(
    ey_table: pd.DataFrame, cluster_lookup: dict, code_name_lookup: dict
):
    """Calculates, for each indicator and location, the gender gap in outcomes
        before boys and girls
    Args:
        ey_table: early years outcomes
        cluster_lookup: lookup between local authority and cluster
        code_name_lookup: lookup between geography code and name

    """

    return (
        ey_table.groupby(["year", "indicator"])
        .apply(
            lambda df: df.pivot_table(
                index="new_la_code", columns="gender", values="score"
            ).assign(ratio=lambda df_2: (df_2["Boys"] / df_2["Girls"]))["ratio"]
        )
        .reset_index(drop=False)
        .assign(cluster=lambda df: df["new_la_code"].map(cluster_lookup))
        .assign(la_name=lambda df: df["new_la_code"].map(code_name_lookup))
        .dropna(axis=0, subset=["cluster"])
    )


def plot_gender_gap_trend(gender_gap_table: pd.DataFrame) -> alt.Chart:
    """Plots evolution in the the gender gap  for LAs in each cluster
    Args:
        gender_gap_table: table with gender gap by location / cluster / year

    """

    all_areas = (
        alt.Chart()
        .mark_line(point=True)
        .encode(
            x="year:N",
            y=alt.Y("ratio", scale=alt.Scale(zero=False)),
            color="cluster:N",
            detail="new_la_code",
            tooltip=["la_name", "ratio"],
        )
    ).properties(width=100, height=100)

    mean = (
        alt.Chart()
        .mark_line(point=False, color="black")
        .encode(
            x="year:N",
            y=alt.Y("median(ratio)", scale=alt.Scale(zero=False), title="Gender ratio"),
        )
    ).properties(width=100, height=100)

    return (
        alt.layer(all_areas, mean, data=gender_gap_table)
        .facet(row="indicator", column="cluster:N")
        .resolve_scale(y="independent")
    )


def plot_gender_gap_comp(gender_gap_table: pd.DataFrame, year: int = 2019) -> alt.Chart:
    """Boxplot comparing gender gap across clusters
    Args:
        gender_gap_table: table with gender gap by location / cluster / year
        year: year to plot
    """

    return (
        alt.Chart(gender_gap_table.query(f"year=={year}"))
        .mark_boxplot()
        .encode(
            y="cluster:N",
            x=alt.X("ratio", scale=alt.Scale(zero=False)),
            column="indicator",
            tooltip=["la_name", "ratio"],
            color="cluster:N",
        )
        .resolve_axis(x="independent")
        .properties(width=200)
    )


def fetch_shapefile():
    """Fetch and save shapefile"""
    shape_url = "https://ons-inspire.esriuk.com/arcgis/rest/services/Administrative_Boundaries/Counties_and_Unitary_Authorities_December_2017_Boundaries_UK/MapServer/0/query?outFields=*&where=1%3D1&f=geojson"

    with open(shape_path, "w") as outfile:
        json.dump(requests.get(shape_url).json(), outfile)


def shapefile():
    """Reads shapefile"""
    return gp.read_file(shape_path)


#
