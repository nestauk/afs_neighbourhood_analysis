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
# # Fingertips PHE indicators

# %%
# %load_ext autoreload

# %%
# %autoreload 2

# %%
import pandas as pd
import numpy as np
import altair as alt
import geopandas as gpd

# %%
from afs_neighbourhood_analysis import PROJECT_DIR

# %%
from afs_neighbourhood_analysis.getters import official

# %%
indicators_df = official.indicator_inventory()

# %%
indicators_df.drop_duplicates(subset=["indicator_id"]).to_csv(
    f"{PROJECT_DIR}/outputs/data/indicators_no_dupes.csv"
)

# %%
