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
import numpy as np
import pandas as pd
import requests
from toolz import pipe
from scipy.stats import ttest_ind

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

# %% [markdown]
# ## Clustering diagnostics

# %%
diag = clustering_diagnostics()

# %%
alt.Chart(diag).mark_point(filled=True).encode(
    x="pca", y="value", row="diagnostic_var", color="comm_resolution:O"
).resolve_scale(y="independent").properties(width=200, height=100)

# %%
pca_mean = (
    diag.groupby(["pca", "diagnostic_var"])["value"].median().reset_index(drop=False)
)

alt.Chart(pca_mean).mark_line(point=True).encode(
    x="pca", y="value", color="diagnostic_var"
).properties(width=200, height=100)

# %%
com_res_mean = (
    diag.groupby(["comm_resolution", "diagnostic_var"])["value"]
    .median()
    .reset_index(drop=False)
)

alt.Chart(com_res_mean).mark_line(point=True).encode(
    x="comm_resolution", y="value", color="diagnostic_var"
).properties(width=200, height=100)

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
phf = public_health_for_clustering()

# %%
clust = extract_clusters(phf, 5, 0.9, clustering_params)

# %%
code_name_lookup = make_code_name_lookup()
code_nut_lookup = get_code_nuts_lookup()

# %%
cluster_df = (
    pd.Series(clust[1])
    .reset_index(name="cluster")
    .assign(geo_name=lambda df: df["index"].map(code_name_lookup))
    .assign(nuts_name=lambda df: df["index"].map(code_nut_lookup))
    .rename(columns={"index": "geo_code"})
)

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
    .encode(y="cluster:O", x="share", color="region")
)
reg_bar

# %% [markdown]
# ### EFSYP performance differences

# %%
clust_lu = cluster_df.set_index("geo_code")["cluster"].to_dict()

# %%
ey_bench = ey.assign(cluster=lambda df: df["new_la_code"].map(clust_lu)).dropna(
    axis=0, subset=["cluster"]
)

# %%
plot_ey_perf(ey_bench, 2019, "Total")

# %%
plot_ey_perf(ey_bench, 2019, "Boys")

# %% [markdown]
# ### Evolution of differences

# %%
plot_ey_evol(ey_bench, gender="Total")

# %% [markdown]
# ### Year on year comparisons

# %%
plot_ey_year_comp(ey_bench)

# %% [markdown]
# ### Differences between clusters

# %%
phf_long = phf_for_analysis(phf, clust_lu, code_name_lookup)

# %%
plot_phf_differences(phf_long, sig_level=0.01)

# %% [markdown]
# ### Improvements in performance inside clusters

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
