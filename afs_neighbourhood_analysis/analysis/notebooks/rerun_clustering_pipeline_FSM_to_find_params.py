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
import os

import altair as alt
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind
import requests
from toolz import pipe

# %%
from afs_neighbourhood_analysis.analysis.feature_selection_scratch import *
from afs_neighbourhood_analysis.pipeline.lad_clustering.conseq_clustering import *

from afs_neighbourhood_analysis.getters.clustering import clustering_diagnostics
from afs_neighbourhood_analysis.pipeline.lad_clustering.cluster_utils import (
    extract_clusters,
    clustering_params,
)
from afs_neighbourhood_analysis.getters.clustering import (
    early_years_for_clustering,
    public_health_for_clustering,
)

from afs_neighbourhood_analysis.pipeline.fetch_ahah import create_ahah

# %%
alt.data_transformers.disable_max_rows()

# %%
pd.set_option('display.max_columns', None)

# %%
elg = el_goals(df_key = "ELG_GLD_add", characteristic="FSM")

ey_indicators = elg["indicator"].unique()

# %%
early_years = pipe(el_goals(df_key = "ELG_GLD_add", characteristic="FSM"), standardise_early_years)

# %%
ahah = create_ahah()

# %%
ahah.drop(columns=[col for col in ahah.columns if "Rank" in col], inplace=True)
ahah.drop(columns=[col for col in ahah.columns if "ah3" in col], inplace=True)
ahah.drop(columns=[col for col in ahah.columns if "Percentiles" in col], inplace=True)

# %%
numeric_cols = ahah.select_dtypes(include=[np.number]).columns
non_numeric = [col for col in ahah.columns if col not in numeric_cols]
ahah_numeric = ahah[numeric_cols].apply(zscore)

# %%
ahah_zcore = pd.concat([ahah[non_numeric], ahah_numeric], axis=1)

# %%
phf = public_health_for_clustering()
cols_to_drop = [col for col in phf.columns if "readiness" in col.lower()]
phf.drop(cols_to_drop, axis=1, inplace=True)

# %%
public_health_profile_ahah = phf.merge(ahah_zcore, left_on="area_code", right_on="CTYUA21CD", how="left").rename(columns={"CTYUA21CD":"area_code"}).set_index("area_code").drop(columns=["CTYUA21NM"])

# %%
search_params = product(range(5, 90, 15), np.arange(0.4, 1.1, 0.1))

clustering_results = [
    clustering_consequential_pipe(
        public_health_profile_ahah,
        param[0],
        param[1],
        early_years,
        clustering_params,
    )
    for param in search_params
]

# %%
with open(
    f"{PROJECT_DIR}/inputs/data/cluster_grid_search_results_fsm_ahah_alt.p", "wb"
) as outfile:
    pickle.dump(clustering_results, outfile)

# %%
clustering_results

# %%
diag = clustering_diagnostics("cluster_grid_search_results_fsm_ahah_alt.p")

# %%
alt.Chart(diag).mark_point(filled=True).encode(
    x="pca", y="value", row="diagnostic_var", color="comm_resolution:O"
).resolve_scale(y="independent")

# %%
pca_mean = (
    diag.groupby(["pca", "diagnostic_var"])["value"].median().reset_index(drop=False)
)

alt.Chart(pca_mean).mark_line(point=True).encode(
    x="pca", y="value", color="diagnostic_var"
)

# %%
com_res_mean = (
    diag.groupby(["comm_resolution", "diagnostic_var"])["value"]
    .median()
    .reset_index(drop=False)
)

alt.Chart(com_res_mean).mark_line(point=True).encode(
    x="comm_resolution", y="value", color="diagnostic_var"
)

# %%
