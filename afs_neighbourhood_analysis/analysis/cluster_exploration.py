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

# %load_ext autoreload
# %autoreload 2

# %% [markdown]
# ## Preamble

# %%
import altair as alt
import io
import json
import numpy as np
import pandas as pd
import requests
from functools import partial
from toolz import pipe
from scipy.stats import ttest_ind

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

from afs_neighbourhood_analysis.utils.altair_utils import altair_text_resize, save_altair, google_chrome_driver_setup


# %% [markdown]
# #### Functions

# %%
def get_county_pop():
    
    url = "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland/mid2020/ukpopestimatesmid2020on2021geography.xls"
    
    with io.BytesIO(requests.get(url).content) as fh:
        return pd.io.excel.read_excel(fh, sheet_name="MYE2 - Persons",skiprows=7).set_index("Code")["All ages"].to_dict()


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
phf = public_health_for_clustering()[[col for col in phf.columns if "readiness" not in col.lower()]]

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
    .assign(population = lambda df: df["index"].map(area_population))
    .rename(columns={"index": "geo_code"})
)

# %%
# Save table
cluster_table = (cluster_df
                 .groupby("cluster")
                 .apply(lambda df: pipe(df.sort_values("population",ascending=False).iloc[:10,:]["geo_name"].tolist(),
                                        lambda _l: ", ".join(_l)+"..."))
                 .reset_index(name="Top 10 C/UAs by population"))
cluster_table.to_markdown(f"{PROJECT_DIR}/outputs/cluster_table.md", index=False)

# %%
# Save cluster to geocode lookup

clust_lu = cluster_df.set_index("geo_code")["cluster"].to_dict()

with open(f"{PROJECT_DIR}/inputs/data/cluster_lookup.json","w") as outfile:
    json.dump(clust_lu,outfile)


# %% [markdown]
# ## Explore cluster results

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
    .encode(y=alt.Y("cluster:O",title="Cluster"), 
            x=alt.X("share",title="% of cluster",axis=alt.Axis(format="%")), 
            color=alt.Color("region",title="Region"))
    .properties(width=400,height=175))

save_altair(altair_text_resize(reg_bar),
            "cluster_nuts",
            driver=wd)

reg_bar

# %% [markdown]
# ### Other sociodemographic differences

# %%
ethn = pd.read_csv("https://www.nomisweb.co.uk/api/v01/dataset/NM_1504_1.data.csv?date=latest&geography=1941962753...1941962984&cell=0...10&measures=20100&select=date_name,geography_name,geography_code,cell_name,measures_name,obs_value,obs_status_name")

# %%
ethn_div = ethn.query("CELL_NAME != 'All categories: Ethnic group'").groupby("GEOGRAPHY_CODE").apply(lambda x: pipe(x["OBS_VALUE"]/x["OBS_VALUE"].sum(),entropy)).to_dict()

cluster_df = (cluster_df
              .assign(ethn_div = lambda df: df["geo_code"].map(ethn_div)))

# %%
# socio-chart

socio = (alt.Chart(cluster_df)
         .mark_point(filled=True,stroke="Grey",strokeWidth=0.8)
         .encode(y=alt.Y("nuts_name:N",title="Region"),
                 x=alt.X("ethn_div",title="Ethnic diversity (entropy)"),
                 color=alt.Color("cluster:N",title="Cluster"),
                 tooltip=["geo_name","cluster"],
                 size=alt.Size("population",title="Population"))
         .properties(width=400,height=195))

save_altair(altair_text_resize(socio),"cluster_demo",driver=wd)

altair_text_resize(socio)


# %% [markdown]
# ### Differences in secondary variables

# %%
phf_long = phf_for_analysis(phf, clust_lu, code_name_lookup)

# %%
save_altair(
    altair_text_resize(plot_phf_differences(phf_long, sig_level=0.01)).properties(width=500, height=250),
    name="second_diffs",driver=wd)

# %%
plot_phf_differences(phf_long, sig_level=0.01)

# %%
# We want to create a table that shows top "negative" and "positive" scores for each cluster
diff_results = (pipe(phf_long, calc_mean_ph)
                .merge(
                    phf_ttest(phf_long, 0.01),
                    left_on=["indicator_name_expanded", "cluster"],
                    right_on=["indicator", "cluster"])
                .assign(mean_all_cs = lambda df: df["indicator_name_expanded"].map(
                    df.groupby("indicator_name_expanded")["mean"].mean()))
                .assign(direction = lambda df: df["mean"] - df["mean_all_cs"])
                .assign(abs_distance = lambda df: pipe(df["direction"],np.absolute))
                .assign(direction_pos = lambda df: df["direction"]>0)
                .query("is_sig==True"))

diff_results.head()

# %%
# Table with most significant differences
cluster_results = (diff_results
                   .groupby("cluster")
                   .apply(lambda df: ", ".join([f"{row['indicator_name_expanded']} ({'+' if row['direction_pos'] else '-'})" for _,row in df.sort_values("abs_distance",ascending=False).iterrows()][:5]))
                   .reset_index(name="Significantly different variables"))
cluster_results.to_markdown(f"{PROJECT_DIR}/outputs/secondary_differences.md",index=False)
cluster_results

# %% [markdown]
# ### EFSYP performance differences

# %%
clean_var_names["average_point_score"] = "1. Average point score"
clean_var_names["comm_lang_lit_percent"] = "2. Communication and language"
clean_var_names["elg_percent"] = "3. Achieved expected goals"
clean_var_names["gld_percent"] = "4. Good level of development"


# %%
clust_lu = cluster_df.set_index("geo_code")["cluster"].to_dict()

# %%
ey_bench = pipe(ey.assign(cluster=lambda df: df["new_la_code"].map(clust_lu)).dropna(
    axis=0, subset=["cluster"]),
                partial(clean_table_names,columns=["indicator"],clean_dict=clean_var_names))

# %%
ey_perf_2019 = plot_ey_perf(ey_bench, 2019, "Total").properties(width=200,height=195)

save_altair(altair_text_resize(ey_perf_2019),"outcomes_2019",driver=wd)

ey_perf_2019

# %%
plot_ey_perf(ey_bench, 2019, "Boys")

# %% [markdown]
# ### Year on year comparisons

# %%
plot_ey_year_comp(ey_bench)

# %% [markdown]
# ### Evolution of differences

# %%
plot_ey_evol(ey_bench, gender="Total")

# %%
# Where have we seen the greatest improvements inside clusters?

# %%
plot_ey_evol(ey_bench, "Girls")

# %%
# Other things to do:
# 1. Calculate SHAPLEY values for variables
# 2. measure gender gap in performance inside clusters
# 3. Create choropleth


# %% [markdown]
# ### Gender gap

# %%
gender_gap = get_gender_gap(ey, clust_lu, code_name_lookup)

# %%
plot_gender_gap_comp(gender_gap, year=2019)

# %%
plot_gender_gap_trend(gender_gap)

# %%
