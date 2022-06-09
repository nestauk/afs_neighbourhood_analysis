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

# %% [markdown]
# ## Clustering

# %%
# %load_ext autoreload

# %%
# %autoreload 2

# %%
# %matplotlib inline

# %%
import pandas as pd
import numpy as np
import altair as alt
import geopandas as gpd

# %%
from afs_neighbourhood_analysis.getters import clustering
from afs_neighbourhood_analysis.utils.utils import nestafont, load_colours
from afs_neighbourhood_analysis.pipeline.lad_clustering import cluster_utils

# %%
colours = load_colours()
for key, val in colours.items():
    if key == "nesta_colours_new":
        nesta_colours = val

# %%
alt.themes.register("nestafont", nestafont)
alt.themes.enable("nestafont")

# %% [markdown]
# ### Clustering diagnostics

# %%
cluster_results = clustering.clustering_diagnostics()

# %%
cluster_results

# %%
cluster_early_years = clustering.early_years_for_clustering()

# %%
cluster_fingertips = clustering.public_health_for_clustering()

# %%
