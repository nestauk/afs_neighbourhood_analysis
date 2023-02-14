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
#     display_name: afs_neighbourhood_analysis
#     language: python
#     name: afs_neighbourhood_analysis
# ---

# %%
# %load_ext autoreload

# %%
# %autoreload 2

# %%
# %matplotlib inline

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
from scipy.stats import ttest_ind, zscore, entropy

# %%
import geopandas as gpd

# %%
from afs_neighbourhood_analysis.utils.utils import nestafont, load_colours, clean_table_names
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

from afs_neighbourhood_analysis.analysis.clustering.clustering_eda import *

from afs_neighbourhood_analysis.analysis.report_analysis import *

from afs_neighbourhood_analysis.utils.altair_utils import (
    altair_text_resize,
    save_altair,
    google_chrome_driver_setup,
)

# %%
colours = load_colours()
nesta_colours = colours["nesta_colours_new"]

# %%
alt.themes.register("nestafont", nestafont)
alt.themes.enable("nestafont")

# %%
nestafont


# %%
def nesta_theme():
    font="Averta"
    return {
        'config': {
            'view': {'continuousHeight': 300, 'continuousWidth': 400},  # from the default theme
            'range': {'category': ['#0F294A', '#0000FF', '#18A48C', '#97D9E3', '#9A1BBE', "#A59BEE", "#F6A4B7", "#EB003B", "#FF6E47", "#FDB633", "#D2C9C0"]},
            "title": {"font": font},
            "axis": {"labelFont": font, "titleFont": font},
            "header": {"labelFont": font, "titleFont": font},
            "legend": {"labelFont": font, "titleFont": font},
        }
    }
alt.themes.register('nesta_theme', nesta_theme)
alt.themes.enable('nesta_theme')

# %% [markdown]
# ## Extract clusters

# %%
clean_var_names = {}

wd = google_chrome_driver_setup()

ey = early_years_for_clustering()
phf = pipe(
    public_health_for_clustering(),
    lambda df: df[[col for col in df.columns if "readiness" not in col.lower()]],
)

clust = get_cluster_lookup()
code_name_lookup = make_code_name_lookup()
code_nut_lookup = get_code_nuts_lookup()
area_population = get_county_pop()

cluster_df = (
    pd.Series(clust)
    .reset_index(name="cluster")
    .assign(geo_name=lambda df: df["index"].map(code_name_lookup))
    .assign(nuts_name=lambda df: df["index"].map(code_nut_lookup))
    .assign(population=lambda df: df["index"].map(area_population))
    .rename(columns={"index": "geo_code"})
)

# Table with top LADs per cluste
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

# %%
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

plt.savefig(f"{PROJECT_DIR}/outputs/figures/png/test.png")

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

#save_altair(altair_text_resize(reg_bar), "cluster_nuts", driver=wd)

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

# %%
cluster_df = cluster_df.assign(ethn_div=lambda df: df["geo_code"].map(ethn_div))

# %%
socio = (
    alt.Chart(cluster_df)
    .mark_point(filled=True, stroke="Grey", strokeWidth=0.8)
    .encode(
        y=alt.Y("nuts_name:N", title="Region"),
        x=alt.X("ethn_div", title="Ethnic diversity (entropy)"),
        color=alt.Color("cluster:N", title="Cluster", scale=alt.Scale(scheme="accent", reverse=True)),
        tooltip=["geo_name", "cluster"],
        size=alt.Size("population", title="Population"),
    )
    .properties(width=400, height=195)
)

# %%
altair_text_resize(socio)

# %% [markdown]
# ### Differences in secondary variables

# %%
phf_long = phf_for_analysis(phf, clust, code_name_lookup)

# %%
indicators_affecting_ey = ['Children in absolute low income families (under 16s)-Persons-<16 yrs', 'Children in relative low income families (under 16s)-Persons-<16 yrs', "Domestic abuse-related incidents and crimes-Persons-16+ yrs",
       'Hospital admissions caused by unintentional and deliberate injuries in children (aged 0-4 years)-Persons-0-4 yrs',
                           'Infant mortality rate-Persons-<1 yr', 'Low birth weight of term babies-Persons->=37 weeks gestational age at birth',
                           'Newborn Hearing Screening - Coverage-Persons-<1 yr',
       'Newborn and Infant Physical Examination Screening - Coverage-Persons-<1 yr', 'Under 18s conception rate / 1,000-Female-<18 yrs']

# %%
phf_ey = phf_long[phf_long.indicator_name_expanded.isin(indicators_affecting_ey)]

# %%
source = pipe(phf_long, calc_mean_ph).merge(
        phf_ttest(phf_long, 0.01, True),
        left_on=["indicator_name_expanded", "cluster"],
        right_on=["indicator", "cluster"],
    ).query("is_sig == True")


# %%
source_ey = source[source.indicator_name_expanded.isin(indicators_affecting_ey)]

# %%
source_ey

# %%
source_ey.loc[-1] = [4, "", 0, 0, 0, "", 0, True]

# %%
alt.Chart(source_ey).mark_rect(filled=True).encode(
    x=alt.X(
        "indicator_name_expanded",
        sort=alt.EncodingSortField("rank", order="descending"),
        axis=alt.Axis(labels=False, ticks=False),
    ),
    y="cluster:N",
    color=alt.Color("mean", scale=alt.Scale(scheme="Redblue", reverse=True)),
    tooltip=["cluster", "indicator_name_expanded", "mean"],
).properties(width=800, height=300)


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

diff_results[diff_results.indicator_name_expanded.isin(indicators_affecting_ey)].head(10)

# %%
cluster_results = (
    diff_results.groupby("cluster")
    .apply(
        lambda df: ", ".join(
            [
                f"{row['indicator_name_expanded']} ({'+' if row['direction_pos'] else '-'})"
                for _, row in df.sort_values("abs_distance", ascending=False).iterrows()
            if row['indicator_name_expanded'] in indicators_affecting_ey][:5]
        )
    )
    .reset_index(name="Significantly different variables")
)

# %%
cluster_results.to_markdown(
    f"{PROJECT_DIR}/outputs/secondary_differences_ey_indicators.md", index=False
)

# %%
list(cluster_results["Significantly different variables"])

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

# %%
ey_perf_2019

# %%
plot_ey_perf(ey_bench, 2019, "Boys")

# %%
phf_ey["indicator_name_expanded"] = phf_ey.indicator_name_expanded.replace({"Children in absolute low income families (under 16s)-Persons-<16 yrs":"Absolute low income", "Children in relative low income families (under 16s)-Persons-<16 yrs":"Relative low income", "Under 18s conception rate / 1,000-Female-<18 yrs":"Under 18s conception rate","Low birth weight of term babies-Persons->=37 weeks gestational age at birth":"Low birth weight (full term)"})

# %%
indicators_chart = alt.Chart(phf_ey[phf_ey.indicator_name_expanded.isin(["Absolute low income", "Relative low income", "Under 18s conception rate", "Low birth weight (full term)"])]
         ).mark_boxplot().encode(
    y="cluster:O",
    color="cluster:N",
    x=alt.X("score", title="Z-score"),
    tooltip=["area_name"],
    column=alt.Column("indicator_name_expanded", sort=["Absolute low income", "Relative low income", "Under 18s conception rate", "Low birth weight (full term)"], title="Indicator")).properties(width=200)

# %%
comparison_indicators_ey = indicators_chart & ey_perf_2019

# %%
comparison_indicators_ey

# %%
save_altair(altair_text_resize(comparison_indicators_ey), "comparison_indicators_ey", driver=wd)


# %% [markdown]
# ### EFSYP differences: pairwise comparisons

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


# %%
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


# %%
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
make_comp_chart(pairwise_comps)

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
    **kwargs
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

    title_of_plot = kwargs.get("title_of_plot", "Average Point Score (normalised)")

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
                title=title_of_plot,
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
plot_outperf(ey_bench, indicator="3. Achieved Expected Level", title_of_plot = "Z-score of children reaching the expected level of development (per cluster)") | plot_outperf(ey_bench, indicator="4. Good Level", title_of_plot = "Z-score of children reaching a good level of development (per cluster)")

# %%
cluster_0_out = ["Richmond upon Thames", "Surrey"]
cluster_0_under = ["Central Bedfordshire", "Cambridgeshire"]
cluster_1_out = ["Stockton-on-Tees", "Medway", "Hartlepool"]
cluster_1_under = ["Leeds", "Dudley"]
cluster_2_out = ["Doncaster", "Barking and Dagenham"]
cluster_2_under = ["Middlesbrough"]
cluster_3_out = ["Gateshead", "South Tyneside", "Sunderland"]
cluster_3_under = ["Halton", "Liverpool"]
cluster_4_out = ["Greenwich"]
cluster_4_under = ["Peterborough"]
cluster_5_out = ["Lewisham", "Wandsworth", "Waltham Forest"]
cluster_5_under = ["Enfield", "Islington", "Hackney", "Tower Hamlets", "Kensington and Chelsea"]
cluster_6_out = ["Bexley", "Trafford", "Northumberland"]
cluster_6_under = ["Lincolnshire", "Stockport", "Bedford Borough"]
cluster_7_out = ["East Sussex", "Herefordshire", "North Somerset", "York"]
cluster_7_under = ["Suffolk", "Cornwall"]

# %%
all_clusters_under_out = cluster_0_out + cluster_0_under + cluster_1_out + cluster_1_under + cluster_2_out + cluster_2_under + cluster_3_out + cluster_3_under + cluster_4_out + cluster_4_under + cluster_5_out + cluster_5_under + cluster_6_out + cluster_6_under + cluster_7_out + cluster_7_under

# %%
all_clusters_out = cluster_0_out + cluster_1_out + cluster_2_out + cluster_3_out + cluster_4_out + cluster_5_out + cluster_6_out + cluster_7_out

# %%
all_clusters_under = cluster_0_under + cluster_1_under + cluster_2_under + cluster_3_under + cluster_4_under + cluster_5_under+ cluster_6_under + cluster_7_under

# %%
phf_ey["indicator_name_expanded"] = phf_ey.indicator_name_expanded.replace({"Hospital admissions caused by unintentional and deliberate injuries in children (aged 0-14 years)-Female-<15 yrs":"Hospital admissions for children (Female)","Hospital admissions caused by unintentional and deliberate injuries in children (aged 0-14 years)-Male-<15 yrs":"Hospital admissions for children (Male)", "Hospital admissions caused by unintentional and deliberate injuries in children (aged 0-14 years)-Persons-<15 yrs": "Hospital admissions for children", "Hospital admissions caused by unintentional and deliberate injuries in children (aged 0-4 years)-Persons-0-4 yrs":"Hospital admissions for children (0-4y)",'Infant mortality rate-Persons-<1 yr': "Infant mortality rate", "Newborn Hearing Screening - Coverage-Persons-<1 yr": "Newborn hearing screening coverage","Newborn and Infant Physical Examination Screening - Coverage-Persons-<1 yr":"<1y physical examination screening coverage", "Domestic abuse-related incidents and crimes-Persons-16+ yrs":"Incidents of domestic abuse"})

# %%
phf_ey_out_under = phf_ey[phf_ey.area_name.isin(all_clusters_under_out)]

# %%
ey_bench_out_under = ey_bench[ey_bench.la_name.isin(all_clusters_under_out)]

# %%
out_under = []
for la_name_ in ey_bench_out_under.la_name:
    if la_name_ in all_clusters_out:
        out_under.append("outperformer")
    else:
        out_under.append("underperformer")

# %%
out_under_phf = []
for la_name_ in phf_ey_out_under.area_name:
    if la_name_ in all_clusters_out:
        out_under_phf.append("outperformer")
    else:
        out_under_phf.append("underperformer")

# %%
phf_ey_out_under["out_under"] = out_under_phf

# %%
ey_bench_out_under["out_under"] = out_under

# %%
ey_bench_out_under_total_2019 = ey_bench_out_under[(ey_bench_out_under.gender == "Total") & (ey_bench_out_under.year == 2019)]

# %%
ey_bench_out_under_total_2019_indicator = ey_bench_out_under_total_2019[ey_bench_out_under_total_2019.indicator == "3. Achieved Expected Level"]

# %%
phf_ey_out_under_ex_level = phf_ey_out_under.merge(ey_bench_out_under_total_2019_indicator[["new_la_code", "indicator", "score", "zscore"]], left_on="area_code", right_on="new_la_code")

# %%
phf_ey_out_under_ex_level["indicator_name_expanded"] = phf_ey_out_under_ex_level.indicator_name_expanded.replace({"Domestic abuse-related incidents and crimes-Persons-16+ yrs":"Incidents of domestic abuse"})

# %%
phf_ey_out_under_ex_level

# %%
cluster_df

# %%
phf_ey_out_under_ex_level = phf_ey_out_under_ex_level.merge(cluster_df[["geo_code","nuts_name","population","ethn_div"]], left_on="area_code", right_on = "geo_code")

# %%
phf_ey_out_under_ex_level.columns


# %%
def out_under(n):
    base = alt.Chart(phf_ey_out_under_ex_level[phf_ey_out_under_ex_level.cluster == n])

    return (base.mark_point().encode(
            x=alt.X('score_x', title='Indicator score'),
            y=alt.Y('indicator_name_expanded', title='Indicator'),
            color=alt.Color('nuts_name', title="Region"),
            tooltip=alt.Tooltip(["indicator_name_expanded","area_name"]),
            shape = alt.Shape("out_under", title="Out/under performer")
        )).properties(title=f"Cluster {n}")


# %%
out_under(5)

# %%
for cluster_ in phf_ey_out_under_ex_level.cluster.unique():
    save_altair(altair_text_resize(out_under(cluster_)), f"cluster_{cluster_}", driver=wd)

# %%
ethnic_div_out_under = cluster_df.merge(ey_bench_out_under[["new_la_code", "out_under"]], left_on="geo_code", right_on = "new_la_code", how="right")

# %%
socio = (
    alt.Chart(ethnic_div_out_under)
    .mark_point(filled=True, stroke="Grey", strokeWidth=0.8)
    .encode(
        y=alt.Y("nuts_name:N", title="Region"),
        x=alt.X("ethn_div", title="Ethnic diversity (entropy)"),
        color=alt.Color("cluster:N", title="Cluster"),
        tooltip=["geo_name", "cluster"],
        size=alt.Size("population", title="Population"),
        shape=alt.Shape("out_under", "Out-/under-performing")
    )
    .properties(width=400, height=195)
)

# %%
save_altair(altair_text_resize(plot_outperf(ey_bench, indicator="3. Achieved Expected Level", title_of_plot = "Z-score of children reaching the expected level of development (per cluster)")), "outperformers_percentage_of_children_reaching_expected_level_of_development", driver=wd)

# %%
col_1=alt.Chart(phf_ey_out_under_ex_level[phf_ey_out_under_ex_level.cluster.isin([0,2])]).mark_point().encode(
    alt.X(
        'score_x:Q',
        title="Indicator score",
        scale=alt.Scale(zero=False),
        axis=alt.Axis(grid=False)
    ),
    alt.Y(
        'indicator_name_expanded:N',
        title="",
        sort='-x',
        axis=alt.Axis(grid=True)
    ),
    tooltip=alt.Tooltip(["area_name"]),
    color=alt.Color('out_under:N', legend=alt.Legend(title="Year")),
    row=alt.Row(
        'cluster:N',
        title="")
).properties(
    height=alt.Step(20)
)

# %%
col_2 = alt.Chart(phf_ey_out_under_ex_level[phf_ey_out_under_ex_level.cluster.isin([1,5])]).mark_point().encode(
    alt.X(
        'score_x:Q',
        title="Indicator score",
        scale=alt.Scale(zero=False),
        axis=alt.Axis(grid=False)
    ),
    alt.Y(
        'indicator_name_expanded:N',
        title="",
        sort='-x',
        axis=alt.Axis(grid=True)
    ),
    tooltip=alt.Tooltip(["area_name"]),
    color=alt.Color('out_under:N', legend=alt.Legend(title="Year")),
    row=alt.Row(
        'cluster:N',
        title="")
).properties(
    height=alt.Step(20)
)

# %%
col_3 = alt.Chart(phf_ey_out_under_ex_level[phf_ey_out_under_ex_level.cluster.isin([6,7])]).mark_point().encode(
    alt.X(
        'score_x:Q',
        title="Indicator score",
        scale=alt.Scale(zero=False),
        axis=alt.Axis(grid=False)
    ),
    alt.Y(
        'indicator_name_expanded:N',
        title="",
        sort='-x',
        axis=alt.Axis(grid=True)
    ),
    tooltip=alt.Tooltip(["area_name"]),
    color=alt.Color('out_under:N', legend=alt.Legend(title="Year")),
    row=alt.Row(
        'cluster:N',
        title="")
).properties(
    height=alt.Step(20)
)

# %%
col_4=alt.Chart(phf_ey_out_under_ex_level[phf_ey_out_under_ex_level.cluster.isin([4])]).mark_point().encode(
    alt.X(
        'score_x:Q',
        title="Indicator score",
        scale=alt.Scale(zero=False),
        axis=alt.Axis(grid=False)
    ),
    alt.Y(
        'indicator_name_expanded:N',
        title="",
        sort='-x',
        axis=alt.Axis(grid=True)
    ),
    tooltip=alt.Tooltip(["area_name"]),
    color=alt.Color('out_under:N', legend=alt.Legend(title="Year")),
    row=alt.Row(
        'cluster:N',
        title="")
).properties(
    height=alt.Step(20)
)

# %%
cluster_1_5_6_7 = (col_2 | col_3).configure_view(stroke="transparent")

# %%
clusters_0_2 = col_1.configure_view(stroke="transparent")

# %%
cluster_4 = col_4.configure_view(stroke="transparent")

# %%
save_altair(altair_text_resize(cluster_4), "cluster_4_indicators", driver=wd)

# %%
asq = pd.read_csv(f"{PROJECT_DIR}/inputs/data/raw/asq_scores.csv")

# %%
phf_ey_out_under_ex_level = phf_ey_out_under_ex_level.merge(asq[["area", "fin_2017_18", "fin_2018_19", "fin_2019_20", "fin_2020_21"]], left_on="area_code", right_on="area")

# %%
alt.Chart(phf_ey_out_under_ex_level[phf_ey_out_under_ex_level.fin_2018_19 != "Suppressed"].drop_duplicates(subset="area_name")).mark_point().encode(
    x="area_name",
    y="fin_2018_19:Q",
    color="out_under",
    column="cluster:N")

# %%
alt.Chart(phf_ey_out_under_ex_level).mark_circle().encode(
    x="fin_2018_19",
    y="score_y")

# %%
county_unitary_authority_boundaries = gpd.read_file(
    f"{PROJECT_DIR}/inputs/data/aux/geodata/Counties_and_Unitary_Authorities_(December_2019)_Boundaries_UK_BUC/Counties_and_Unitary_Authorities_(December_2019)_Boundaries_UK_BUC.shp"
).to_crs(epsg=4326)

# %%
county_unitary_authority_boundaries = county_unitary_authority_boundaries[county_unitary_authority_boundaries.ctyua19cd.str.contains("E")]

# %%
shape_out_under = county_unitary_authority_boundaries.merge(ey_bench_out_under[["new_la_code", "out_under", "cluster"]], left_on="ctyua19cd", right_on="new_la_code")

# %%
shape_out_under.drop_duplicates(inplace=True)

# %%
cluster_ = 0
shape_out_under_cluster = shape_out_under[shape_out_under.cluster == cluster_]

# %%
shape_not_either = county_unitary_authority_boundaries[~county_unitary_authority_boundaries.ctyua19nm.isin(list(shape_out_under_cluster.ctyua19nm.unique()))]

# %%
shape_not_either["out_under"] = "neither"

# %%
shape_out_under_cluster = gpd.GeoDataFrame(pd.concat([shape_out_under_cluster, shape_not_either]),geometry = "geometry")

# %%
london_boroughs = pd.read_csv(f"{PROJECT_DIR}/inputs/data/aux/geodata/london_boroughs.csv")

# %%
color = alt.Color("out_under:N", scale=alt.Scale(domain=["outperformer","underperformer","neither"], range=["#18A48C", "#EB003B", "#D2C9C0"]))

choro_no_london = (
    alt.Chart(
        shape_out_under_cluster[
            ~shape_out_under_cluster.ctyua19cd.isin(list(london_boroughs.lad19cd))
        ]
    )
    .mark_geoshape(stroke="black")
    .encode(
        color=color,
        tooltip=[
            alt.Tooltip("ctyua19nm:N", title="LA"),
            alt.Tooltip("cluster:N", title="Cluster")
        ],
    )
    .properties(width=500, height=600)
)

choro_london = (
    alt.Chart(
        shape_out_under_cluster[
            shape_out_under_cluster.ctyua19cd.isin(list(london_boroughs.lad19cd))
        ]
    )
    .mark_geoshape(stroke="black")
    .encode(
        color=color,
        tooltip=[
            alt.Tooltip("ctyua19nm:N", title="LA"),
            alt.Tooltip("cluster:N", title="Cluster"),
        ],
    )
    .properties(width=300, height=250)
)

# %%
choro_london.configure_view(strokeWidth=0)

# %%
choro_no_london.configure_view(strokeWidth=0)

# %%

# %%
