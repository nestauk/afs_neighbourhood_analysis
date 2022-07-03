# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     comment_magics: true
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Exploratory cluster analysis

# %%
# Exploratory cluster analysis
# %matplotlib inline
# %load_ext autoreload
# %autoreload 2

# %% [markdown]
# ## Preamble

# %%
from itertools import product
import altair as alt
import io
import json
import numpy as np
import pandas as pd
import requests
from functools import partial
from toolz import pipe
from scipy.stats import ttest_ind, zscore

from afs_neighbourhood_analysis import PROJECT_DIR
from afs_neighbourhood_analysis.getters.clustering import clustering_diagnostics
from afs_neighbourhood_analysis.pipeline.lad_clustering.cluster_utils import (
    extract_clusters,
    clustering_params,
)
from afs_neighbourhood_analysis.getters.clustering import (
    early_years_for_clustering,
    public_health_for_clustering,
)

from scipy.stats import entropy

from afs_neighbourhood_analysis.utils.utils import clean_table_names

from afs_neighbourhood_analysis.analysis.clustering.clustering_eda import *

from afs_neighbourhood_analysis.utils.altair_utils import (
    altair_text_resize,
    save_altair,
    google_chrome_driver_setup,
)


# %% [markdown]
# #### Functions

# %%
def get_county_pop():

    url = "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland/mid2020/ukpopestimatesmid2020on2021geography.xls"

    with io.BytesIO(requests.get(url).content) as fh:
        return (
            pd.io.excel.read_excel(fh, sheet_name="MYE2 - Persons", skiprows=7)
            .set_index("Code")["All ages"]
            .to_dict()
        )


# %% [markdown]
# #### Clean variable names lookup

# %%
clean_var_names = {}

# %% [markdown]
# #### Save chart set up

# %%
wd = google_chrome_driver_setup()

# %% [markdown]
# ## Extract clusters

# %%
from afs_neighbourhood_analysis.analysis.feature_selection_scratch import remove_missing
from afs_neighbourhood_analysis.pipeline.lad_clustering.cluster_utils import parse_phf
from afs_neighbourhood_analysis.pipeline.lad_clustering.conseq_clustering import (
    most_recent_data,
)

# %%
ey = early_years_for_clustering()
phf = public_health_for_clustering()[
    [col for col in phf.columns if "readiness" not in col.lower()]
]

# %%
clust = extract_clusters(phf, 5, 0.7, clustering_params)

# %%
code_name_lookup = make_code_name_lookup()
code_nut_lookup = get_code_nuts_lookup()

# %%
area_population = get_county_pop()

# %%
cluster_df = (
    pd.Series(clust[1])
    .reset_index(name="cluster")
    .assign(geo_name=lambda df: df["index"].map(code_name_lookup))
    .assign(nuts_name=lambda df: df["index"].map(code_nut_lookup))
    .assign(population=lambda df: df["index"].map(area_population))
    .rename(columns={"index": "geo_code"})
)

# %%
# Save table
cluster_table = (
    cluster_df.groupby("cluster")
    .apply(
        lambda df: pipe(
            df.sort_values("population", ascending=False)
            .iloc[:10, :]["geo_name"]
            .tolist(),
            lambda _l: ", ".join(_l) + "...",
        )
    )
    .reset_index(name="Top 10 C/UAs by population")
)
cluster_table.to_markdown(f"{PROJECT_DIR}/outputs/cluster_table.md", index=False)

# %%
# Save cluster to geocode lookup

clust_lu = cluster_df.set_index("geo_code")["cluster"].to_dict()

with open(f"{PROJECT_DIR}/inputs/data/cluster_lookup.json", "w") as outfile:
    json.dump(clust_lu, outfile)


# %% [markdown]
# ## Explore cluster results

# %% [markdown]
# ### Choropleth

# %%
from afs_neighbourhood_analysis.analysis.clustering.clustering_eda import shapefile
from afs_neighbourhood_analysis.utils.altair_utils import choro_plot
import json
import matplotlib.pyplot as plt

# %%
shape = (
    shapefile()
    .assign(cluster=lambda df: df["ctyua17cd"].map(clust_lu))
    .dropna(axis=0, subset=["cluster"])
)

# %%
fig, ax = plt.subplots(figsize=(10, 10))

shape.plot(
    column="cluster",
    cmap="Accent_r",
    edgecolor="white",
    linewidth=0.1,
    ax=ax,
    legend=True,
    categorical=True,
    legend_kwds={"title": "Cluster", "fontsize": 14, "title_fontsize": 18},
)
plt.axis("off")
# ax.legend(title="Cluster")
ax.set_title("Map of cluster assignments", size=18)
plt.tight_layout()

plt.savefig(f"{PROJECT_DIR}/outputs/figures/png/cluster_map.png")

# %% [markdown]
# ### Regional differences

# %%
clust_region_shares = (
    cluster_df.groupby("cluster")["nuts_name"]
    .apply(lambda x: x.value_counts(normalize=True))
    .unstack()
    .fillna(0)
    .stack()
    .reset_index(name="share")
    .rename(columns={"level_1": "region"})
)
reg_bar = (
    alt.Chart(clust_region_shares)
    .mark_bar()
    .encode(
        y=alt.Y("cluster:O", title="Cluster"),
        x=alt.X("share", title="% of cluster", axis=alt.Axis(format="%")),
        color=alt.Color("region", title="Region"),
    )
    .properties(width=400, height=175)
)

save_altair(altair_text_resize(reg_bar), "cluster_nuts", driver=wd)

reg_bar

# %% [markdown]
# ### Other sociodemographic differences

# %%
ethn = pd.read_csv(
    "https://www.nomisweb.co.uk/api/v01/dataset/NM_1504_1.data.csv?date=latest&geography=1941962753...1941962984&cell=0...10&measures=20100&select=date_name,geography_name,geography_code,cell_name,measures_name,obs_value,obs_status_name"
)

# %%
ethn_div = (
    ethn.query("CELL_NAME != 'All categories: Ethnic group'")
    .groupby("GEOGRAPHY_CODE")
    .apply(lambda x: pipe(x["OBS_VALUE"] / x["OBS_VALUE"].sum(), entropy))
    .to_dict()
)

cluster_df = cluster_df.assign(ethn_div=lambda df: df["geo_code"].map(ethn_div))

# %%
# socio-chart

socio = (
    alt.Chart(cluster_df)
    .mark_point(filled=True, stroke="Grey", strokeWidth=0.8)
    .encode(
        y=alt.Y("nuts_name:N", title="Region"),
        x=alt.X("ethn_div", title="Ethnic diversity (entropy)"),
        color=alt.Color("cluster:N", title="Cluster"),
        tooltip=["geo_name", "cluster"],
        size=alt.Size("population", title="Population"),
    )
    .properties(width=400, height=195)
)

save_altair(altair_text_resize(socio), "cluster_demo", driver=wd)

altair_text_resize(socio)


# %% [markdown]
# ### Differences in secondary variables

# %%
phf_long = phf_for_analysis(phf, clust_lu, code_name_lookup)

# %%
save_altair(
    altair_text_resize(plot_phf_differences(phf_long, sig_level=0.01)).properties(
        width=500, height=250
    ),
    name="second_diffs",
    driver=wd,
)

# %%
plot_phf_differences(phf_long, sig_level=0.01)

# %%
# We want to create a table that shows top "negative" and "positive" scores for each cluster
diff_results = (
    pipe(phf_long, calc_mean_ph)
    .merge(
        phf_ttest(phf_long, 0.01),
        left_on=["indicator_name_expanded", "cluster"],
        right_on=["indicator", "cluster"],
    )
    .assign(
        mean_all_cs=lambda df: df["indicator_name_expanded"].map(
            df.groupby("indicator_name_expanded")["mean"].mean()
        )
    )
    .assign(direction=lambda df: df["mean"] - df["mean_all_cs"])
    .assign(abs_distance=lambda df: pipe(df["direction"], np.absolute))
    .assign(direction_pos=lambda df: df["direction"] > 0)
    .query("is_sig==True")
)

diff_results.head()

# %%
# Table with most significant differences
cluster_results = (
    diff_results.groupby("cluster")
    .apply(
        lambda df: ", ".join(
            [
                f"{row['indicator_name_expanded']} ({'+' if row['direction_pos'] else '-'})"
                for _, row in df.sort_values("abs_distance", ascending=False).iterrows()
            ][:5]
        )
    )
    .reset_index(name="Significantly different variables")
)
cluster_results.to_markdown(
    f"{PROJECT_DIR}/outputs/secondary_differences.md", index=False
)
cluster_results

# %% [markdown]
# ### EFSYP performance differences

# %%
clean_var_names["average_point_score"] = "1. Avg. point score"
clean_var_names["comm_lang_lit_percent"] = "2. Comm. and Lang."
clean_var_names["elg_percent"] = "3. Achieved Expected Level"
clean_var_names["gld_percent"] = "4. Good Level"


# %%
clust_lu = cluster_df.set_index("geo_code")["cluster"].to_dict()

# %%
ey_bench = pipe(
    ey.assign(cluster=lambda df: df["new_la_code"].map(clust_lu)).dropna(
        axis=0, subset=["cluster"]
    ),
    partial(clean_table_names, columns=["indicator"], clean_dict=clean_var_names),
)

# %%
ey_perf_2019 = plot_ey_perf(ey_bench, 2019, "Total").properties(width=200, height=195)

save_altair(altair_text_resize(ey_perf_2019), "outcomes_2019", driver=wd)

ey_perf_2019

# %%
plot_ey_perf(ey_bench, 2019, "Boys")

# %%
# EFSYP differences: pairwise comparisons


# %%
def t_test(ey, pairs, indicator, var_name="score"):
    """T test between scores in an indicator between pairs of clusters"""

    t = ttest_ind(
        ey.query(f"cluster=={pairs[0]}").query(f"indicator=='{indicator}'")[var_name],
        ey.query(f"cluster=={pairs[1]}").query(f"indicator=='{indicator}'")[var_name],
    )

    mean_diff = (
        ey.query(f"cluster=={pairs[0]}")
        .query(f"indicator=='{indicator}'")[var_name]
        .mean()
        - ey.query(f"cluster=={pairs[1]}")
        .query(f"indicator=='{indicator}'")[var_name]
        .mean()
    )

    return t, mean_diff


def make_pairwise_combs(
    table: pd.DataFrame,
    indicator: str,
    year: int,
    num_clusters: int = 8,
    var_name="score",
):
    """Creates pairwise comparisons of means between the C/UAs in
    different clusters.
    Args:
        table: table of results
        indicator: Indicator we use for the comparison
        year: year to focus on
    """

    cluster_combs = list(product(range(0, num_clusters), range(0, num_clusters)))

    results = []

    for pair in cluster_combs:

        if pair[0] == pair[1]:
            results.append([pair[0], pair[1], np.nan, np.nan])
            results.append([pair[1], pair[0], np.nan, np.nan])
        else:

            t, mean_diff = t_test(
                table.query(f"year=={year}"), pair, indicator, var_name
            )

            results.append([pair[1], pair[0], mean_diff, t.pvalue])
            results.append([pair[0], pair[1], -mean_diff, t.pvalue])

    return pd.DataFrame(
        results, columns=["cluster_1", "cluster_2", "diff_means", "pvalue"]
    )


def make_comp_chart(pair_table: pd.DataFrame, sig_thres: float = 0.05, col_thres=1.5):
    """Creates matrix with comparisons between variables"""

    comp_chart_color = (
        alt.Chart(pair_table.query(f"pvalue<{sig_thres}"))
        .mark_rect(stroke="black")
        .encode(
            x=alt.X("cluster_1:N", title="Cluster 2"),
            y=alt.Y("cluster_2:N", title="Cluster 1"),
            color=alt.Color(
                "diff_means",
                title="Difference in means",
                scale=alt.Scale(scheme="redblue", domainMid=0, reverse=True),
            ),
        )
    ).properties(width=400, height=200)

    comp_chart_text = (
        alt.Chart(pair_table)
        .mark_text()
        .encode(
            x=alt.X("cluster_1:N"),
            y=alt.Y("cluster_2:N"),
            text=alt.Text("diff_means", format=".3f"),
            color=alt.condition(
                abs(alt.datum.diff_means) > col_thres,
                alt.value("white"),
                alt.value("black"),
            ),
        )
    )

    return comp_chart_color + comp_chart_text


# %%
pairwise_comps = make_pairwise_combs(
    ey_bench.query(f"gender=='Total'"), "1. Avg. point score", 2019
)

# %%
save_altair(
    altair_text_resize(make_comp_chart(pairwise_comps, col_thres=1.7)),
    "pairwise",
    driver=wd,
)

# %%
make_comp_chart(pairwise_comps)

# %% [markdown]
# ### Year on year comparisons

# %%
save_altair(
    altair_text_resize(plot_ey_year_comp(ey_bench)), "year_comparisons", driver=wd
)

# %%
# Spearman correlation between cluster ranks in 2013 and 2019
ey_bench.query("indicator=='1. Avg. point score'").query("gender=='Total'").groupby(
    ["cluster", "year"]
)["zscore"].median().unstack(level=1).rank()[[2013, 2019]].corr(method="spearman")


# %% [markdown]
# ### Outperforming and underperforming

# %%
def add_jitter(scale=10):
    """Add some jitter to remove overlaps"""

    return np.random.normal(0, 1) / scale


# %%
def plot_outperf(
    perf_table: pd.DataFrame,
    indicator: str = "1. Avg. point score",
    gender: str = "Total",
    year: int = 2019,
    sd_scale: float = 1.2,
    var_name="score",
):
    """Visualises distribution of performance by cluster and
    shows "out and underperformers"
    Args:
        perf_table: table with performance indicators
        indicator: focus indicator
        gender: gender category
        year: year
        sd_scale: standard deviation from the mean that defines
            out / under-performing
    """

    ey_renorm = (
        perf_table.query(f"year=={year}")
        .query(f"gender=='{gender}'")
        .query(f"indicator=='{indicator}'")
        .groupby("cluster")
        .apply(
            lambda df: df.assign(score_in_cluster=lambda df_2: zscore(df_2[var_name]))
        )
        .assign(
            score_in_cluster=lambda df: [
                float(x + add_jitter()) for x in df["score_in_cluster"]
            ]
        )
        .reset_index(drop=True)
        .assign(
            outp=lambda df: [
                r["la_name"] if abs(r["score_in_cluster"]) > sd_scale else ""
                for _, r in df.iterrows()
            ]
        )
    )

    out_under = (
        alt.Chart(ey_renorm)
        .mark_point(filled=True, stroke="black", strokeWidth=0.1)
        .encode(  # x=alt.X("cluster:O",scale=alt.Scale(domain=[-1,8])),
            x=alt.X("cluster:O", title="Cluster"),
            # y="score_in_cluster",
            y=alt.Y(
                "score_in_cluster", scale=alt.Scale(type="symlog", domain=[-2.5, 3])
            ),
            color=alt.Color(
                "score_in_cluster", scale=alt.Scale(scheme="redblue"), sort="descending"
            ),
            tooltip=["la_name"],
        )
    ).properties(width=700, height=800)

    out_under_names = (
        alt.Chart(ey_renorm)
        .mark_text(align="left", baseline="middle", dx=6, angle=360)
        .encode(
            x="cluster:O",
            y=alt.Y(
                "score_in_cluster",
                scale=alt.Scale(type="symlog", domain=[-2, 3]),
                title="Average point score (normalised)",
            ),
            # y="score_in_cluster",
            text="outp",
            color=alt.Color(
                "score_in_cluster",
                scale=alt.Scale(scheme="redblue"),
                sort="descending",
                title=["Score in cluster", "(Normalised)"],
            ),
            tooltip=["la_name"],
        )
    ).properties(width=700, height=800)

    return out_under + out_under_names


# %%
save_altair(altair_text_resize(plot_outperf(ey_bench)), "outperforming", driver=wd)

# %%
plot_outperf(ey_bench)

# %% [markdown]
# ### Evolution of differences

# %%
save_altair(
    altair_text_resize(plot_ey_evol(ey_bench, gender="Total")), "year_evol", driver=wd
)

# %%
plot_ey_evol(ey_bench, gender="Total")

# %% [markdown]
# #### testing differences

# %%
import statsmodels.api as sm


# %%
def trend_analysis(table, indicator="1. Avg. point score", gender="Total"):
    """Output linear trend analysis by local authority"""

    sel_t = (
        table.query(f"indicator=='{indicator}'")
        .query(f"gender=='{gender}'")
        .reset_index(drop=True)
    )

    trends = {}

    for area in sel_t["new_la_code"].unique():

        area_t = sel_t.query(f"new_la_code=='{area}'")

        model = sm.OLS(area_t["zscore"].values, sm.add_constant(area_t["year"].values))
        results = model.fit()
        trends[area] = results.params[1] if len(results.params) > 1 else np.nan

    return trends


def get_high_std_lads(trend_df, scale=1.2):
    """ """

    return (
        trend_df.groupby("cluster")
        .apply(
            lambda df: (
                df.assign(
                    feature_name=lambda df_2: [
                        row["name"]
                        if abs(row["trend_coeff"])
                        > abs(df["trend_coeff"].mean())
                        + scale * df["trend_coeff"].std()
                        else np.nan
                        for _, row in df_2.iterrows()
                    ]
                )
            )
        )
        .reset_index(drop=True)
        .set_index("la_code")["feature_name"]
        .dropna()
        .to_dict()
    )


def plot_outperf_trend(perf_coeff_table):
    """Plot outperforming / underperforming areas based on their trend"""

    points = (
        alt.Chart()
        .mark_point(filled=True, stroke="black", strokeWidth=0.2)
        .encode(
            x=alt.X("x_pos", title=None, axis=alt.Axis(ticks=False, labels=False)),
            y="trend_coeff",
            tooltip=["name", "trend_coeff"],
            color=alt.Color(
                "trend_coeff",
                scale=alt.Scale(scheme="redblue"),
                sort="descending",
                legend=None,
            ),
        )
        .properties(width=50, height=400)
    )

    mean_all = alt.Chart().mark_rule(strokeWidth=2).encode(y="mean(trend_coeff)")

    mean_cluster = (
        alt.Chart()
        .mark_rule(color="red", strokeDash=[3, 3], strokeWidth=2)
        .encode(y=alt.datum(mean_trend))
    )

    text = (
        alt.Chart()
        .mark_text(align="center", baseline="bottom", dx=6, dy=-5, angle=360)
        .encode(
            x=alt.X("x_pos", title=None, axis=alt.Axis(ticks=False, labels=False)),
            y=alt.Y("trend_coeff", title="Trend coefficient"),
            text="has_name",
            color=alt.Color(
                "trend_coeff",
                scale=alt.Scale(scheme="redblue"),
                sort="descending",
                legend=None,
            ),
        )
    )

    return (
        alt.layer(points, mean_all, mean_cluster, text, data=trend_df)
        .facet("cluster", spacing={"column": 0}, columns=4)
        .resolve_scale(color="independent")
    )


# %%
trend_df = (
    pd.Series(trend_analysis(ey_bench))
    .reset_index(name="trend_coeff")
    .rename(columns={"index": "la_code"})
    .assign(cluster=lambda df: df["la_code"].map(clust_lu))
    .assign(name=lambda df: df["la_code"].map(code_name_lookup))
    .assign(x_pos=lambda df: [0 + add_jitter(scale=1000) for _ in range(len(df))])
    .assign(has_name=lambda df: df["la_code"].map(get_high_std_lads(df, 1)).fillna(""))
    .assign(trend_coeff_2=lambda df: [x + add_jitter() for x in df["trend_coeff"]])
)


# %%
mean_trend = trend_df["trend_coeff"].mean()

# %%
save_altair(
    altair_text_resize(plot_outperf_trend(trend_df)), name="reg_comparison", driver=wd
)

plot_outperf_trend(trend_df)


# %% [markdown]
# ### Gender gap

# %%
gender_gap = pipe(
    get_gender_gap(ey, clust_lu, code_name_lookup),
    partial(clean_table_names, columns=["indicator"], clean_dict=clean_var_names),
)


# %%
pipe(
    plot_gender_gap_comp(gender_gap, year=2019).properties(width=200, height=195),
    altair_text_resize,
    partial(save_altair, name="gender_snapshot", driver=wd),
)

plot_gender_gap_comp(gender_gap, year=2019).resolve_scale(x="independent")

# %%
pairwise_comps_gender = make_pairwise_combs(
    gender_gap, "1. Avg. point score", 2019, var_name="ratio"
)

save_altair(
    altair_text_resize(make_comp_chart(pairwise_comps_gender, col_thres=0.01)),
    "gender_difference_comparison",
    driver=wd,
)

make_comp_chart(pairwise_comps_gender, col_thres=0.01)

# %%
# def plot_gender_diff(gen)

gender_gap_2 = (
    gender_gap.groupby(["cluster", "year"])
    .apply(lambda df: df.assign(zscore=lambda df_2: zscore(df_2["ratio"])))
    .assign(
        name=lambda df: [
            row["la_name"] if abs(row["zscore"]) > 1.5 else " "
            for _, row in df.iterrows()
        ]
    )
    .reset_index(drop=True)
    .groupby(["cluster", "indicator", "year"])
    .apply(
        lambda df: df.assign(
            has_name=lambda df_2: [
                row["la_name"]
                if (row["ratio"] < np.mean(df_2["ratio"]) - 1.2 * np.std(df_2["ratio"]))
                | (row["ratio"] > np.mean(df_2["ratio"]) + 1.2 * np.std(df_2["ratio"]))
                else ""
                for _, row in df_2.iterrows()
            ]
        )
    )
    .reset_index(drop=True)
)


# %%
def plot_gender_differences(gender_table, year, indicator="1. Avg. point score"):
    """Plots differences between genders"""

    rel_data = data = gender_table.query(f"year=={year}").query(
        f"indicator=='{indicator}'"
    )

    gender_point = (
        alt.Chart()
        .mark_point(filled=True, stroke="black", strokeWidth=0.1)
        .encode(
            y=alt.Y(
                "ratio",
                scale=alt.Scale(zero=False),
                title="Ratio between boys and girls scores",
            ),
            tooltip=["la_name", alt.Tooltip("ratio", format=".3f")],
            color=alt.Color(
                "ratio",
                scale=alt.Scale(scheme="redblue"),
                sort="descending",
                title=["Ratio between", "boys and girls"],
            ),
        )
    ).properties(height=400, width=100)
    gender_text = (
        alt.Chart()
        .mark_text(align="center", baseline="bottom", dx=6, dy=-5)
        .encode(
            y=alt.Y("ratio", scale=alt.Scale(zero=False)),
            text="has_name",
            color=alt.Y("ratio", scale=alt.Scale(scheme="redblue"), sort="descending"),
        )
    )

    gender_mean = (
        alt.Chart().mark_rule(color="black", strokeWidth=2).encode(y="mean(ratio)")
    )

    all_mean = (
        alt.Chart()
        .mark_rule(color="red", strokeWidth=2, strokeDash=[3, 3])
        .encode(y=alt.datum(rel_data["ratio"].mean()))
    )

    return alt.layer(
        gender_point, gender_text, gender_mean, all_mean, data=rel_data
    ).facet("cluster", columns=4)


# %%
save_altair(
    altair_text_resize(plot_gender_differences(gender_gap_2, 2019)),
    "gender_gap_clusters",
    driver=wd,
)

plot_gender_differences(gender_gap_2, 2019)

# %%
pipe(
    plot_gender_gap_trend(gender_gap),
    altair_text_resize,
    partial(save_altair, name="gender_trend", driver=wd),
)

plot_gender_gap_trend(gender_gap)

# %%
gender_gap.head()

# %%
gender_gap_3 = (
    gender_gap.query("indicator=='1. Avg. point score'")
    .assign(
        period=lambda df: [
            "first_period" if y < 2016 else "second_period" for y in df["year"]
        ]
    )
    .groupby(["la_name", "indicator", "period", "new_la_code"])
    .apply(lambda df: df.assign(mean_score=df["ratio"].mean()))
    .reset_index(drop=True)
    .pivot_table(
        index=["cluster", "la_name", "new_la_code"],
        columns="period",
        values="mean_score",
    )
    .assign(
        score_ratio=lambda df: [x for x in df["second_period"] / df["first_period"]]
    )
    .reset_index(drop=False)
    .drop(axis=1, labels=["first_period", "second_period"])
    .groupby("cluster")
    .apply(
        lambda df: df.assign(
            has_name=lambda df_2: [
                row["la_name"]
                if (
                    row["score_ratio"]
                    < np.mean(df_2["score_ratio"]) - 1.3 * np.std(df_2["score_ratio"])
                )
                | (
                    row["score_ratio"]
                    > np.mean(df_2["score_ratio"]) + 1.3 * np.std(df_2["score_ratio"])
                )
                else ""
                for _, row in df_2.iterrows()
            ]
        )
    )
    .reset_index(drop=True)
)

# %%
outp_gender_chart = (
    alt.Chart()
    .mark_point(filled=True, strokeWidth=1, stroke="grey")
    .encode(
        y=alt.Y(
            "score_ratio",
            scale=alt.Scale(zero=False),
            title=["Gender parity in", "2017-2019 vs 2013-2016"],
        ),
        tooltip=["la_name", alt.Tooltip("score_ratio", format=".3f")],
        color=alt.Y(
            "score_ratio",
            scale=alt.Scale(scheme="redblue"),
            sort="descending",
            title=["Gender parity in", "2017-2019 vs 2013-2016"],
        ),
    )
    .properties(height=400, width=100)
)

outp_gender_mean = (
    alt.Chart()
    .mark_rule(stroke="black", strokeWidth=3)
    .encode(y="median(score_ratio)", tooltip=["median(score_ratio)"])
)

outp_gender_mean_all = (
    alt.Chart()
    .mark_rule(stroke="red", strokeWidth=3, strokeDash=[2, 2])
    .encode(y=alt.datum(gender_gap_3["score_ratio"].mean()))
)


outp_gender_text = (
    alt.Chart()
    .mark_text(align="center", baseline="bottom", dx=6, dy=-5)
    .encode(
        y=alt.Y("score_ratio", scale=alt.Scale(zero=False)),
        text="has_name",
        color=alt.Y(
            "score_ratio", scale=alt.Scale(scheme="redblue"), sort="descending"
        ),
    )
)

trend_comp = alt.layer(
    outp_gender_chart,
    outp_gender_mean,
    outp_gender_mean_all,
    outp_gender_text,
    data=gender_gap_3,
).facet("cluster", columns=4)

save_altair(altair_text_resize(trend_comp), "gender_parity_evolution", driver=wd)

trend_comp

# %%
# Combine everything

trends_merged = trend_df.merge(
    gender_gap_3, left_on=["la_code"], right_on=["new_la_code"]
)

merged = (
    alt.Chart(trends_merged)
    .mark_point(filled=True, stroke="grey", strokeWidth=0.5)
    .encode(
        x=alt.X(
            "trend_coeff",
            scale=alt.Scale(zero=False),
            title=["Trend coefficient", "in average point score"],
        ),
        y=alt.Y(
            "score_ratio",
            scale=alt.Scale(zero=False),
            title=["Gender parity in", "2017-2019 vs 2013-2016"],
        ),
        color=alt.Color("cluster_x:N", title="Cluster"),
        tooltip="la_name",
    )
)
merged


# %%
# Outperforming integrated
