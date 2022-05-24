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
from scipy.stats import ttest_ind
import pandas as pd
import requests
from toolz import pipe

from afs_neighbourhood_analysis.getters.clustering import clustering_diagnostics
from afs_neighbourhood_analysis.pipeline.lad_clustering.cluster_utils import extract_clusters, clustering_params
from afs_neighbourhood_analysis.getters.clustering import early_years_for_clustering, public_health_for_clustering


# %%
def fetch_geojson(url):
    
    return pipe(requests
                .get(url),
                lambda req: [e["properties"] for e in req.json()["features"]],
                pd.DataFrame,
               )

def make_code_name_lookup():
    
    county_json = pipe(fetch_geojson(
        "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/CTY_APR_2019_EN_NC/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"),
                       lambda df: df.set_index("CTY19CD")["CTY19NM"].to_dict())
    
    lad_json = (pd.read_excel("https://www.arcgis.com/sharing/rest/content/items/c4f647d8a4a648d7b4a1ebf057f8aaa3/data")
                .set_index(["LAD21CD"])["LAD21NM"]
                .to_dict())
    
    return {**county_json, **lad_json}

def get_code_nuts_lookup():
        
    lad_nuts = (pd.read_excel("https://www.arcgis.com/sharing/rest/content/items/c110087ae04a4cacb4ab0aef960936ce/data")
              .set_index("LAD20CD")["ITL121NM"]
              .to_dict())
    
    lad_county = pipe(
        fetch_geojson("https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LAD21_CTY21_EN_LU/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"),
        lambda df: df.set_index("LAD21CD")["CTY21CD"])
    
    
    return {**{code:name for code,name in lad_nuts.items()},
           **{lad_county[lad]:lad_nuts[lad] for lad in set(lad_county.keys())}}


def plot_ey_perf(ey, year,gender):
    """
    """
    
    return (alt.Chart(ey.query(f"year=={year}").query(f"gender=='{gender}'"))
        .mark_boxplot()
        .encode(y="cluster:O",
                x="zscore",
                tooltip=["la_name"],
                column="indicator")).properties(width=200)
            
def plot_ey_trend(ey, gender="Total"):
    """
    """
    
    return (alt.Chart(ey_bench.query(f"gender=='{gender}'"))
            .mark_boxplot()
            .encode(x="year:O",y="zscore",column="cluster",color="cluster:N",
                    row="indicator",
                    tooltip=["la_name","cluster"])).properties(width=100,height=100)
    
def plot_ey_year_comp(ey,gender="Total"):
    """
    """
    
    return (alt.Chart(ey_bench.query(f"gender=='{gender}'"))
            .mark_boxplot()
            .encode(column="year:O",y="zscore",x="cluster:N",color="cluster:N",
                    row="indicator",
                    tooltip=["la_name","cluster"])).properties(width=100,height=100)
    

def plot_ey_evol(ey_table, gender):
    """
    """
    
    return (alt.Chart(ey_table.query(f"gender=='{gender}'"))
            .mark_line(point=True)
            .encode(x="year",y="zscore",color="cluster:N",
                    row="indicator",column="cluster",
                    detail="la_name",tooltip=["la_name","year","zscore"])
            .properties(width=100,height=100))
    


# %% [markdown]
# ## Clustering diagnostics

# %%
diag = clustering_diagnostics()

# %%
alt.Chart(diag).mark_point(filled=True).encode(x="pca",y="value",row="diagnostic_var",
                                            color="comm_resolution:O").resolve_scale(y="independent")

# %%
pca_mean = diag.groupby(["pca","diagnostic_var"])["value"].median().reset_index(drop=False)

alt.Chart(pca_mean).mark_line(point=True).encode(x="pca",y="value",color="diagnostic_var")

# %%
com_res_mean = diag.groupby(["comm_resolution","diagnostic_var"])["value"].median().reset_index(drop=False)

alt.Chart(com_res_mean).mark_line(point=True).encode(x="comm_resolution",y="value",color="diagnostic_var")

# %% [markdown]
# ## Extract clusters

# %%
ey = early_years_for_clustering()
phf = public_health_for_clustering()

# %%
clust = extract_clusters(phf,5,0.9,clustering_params)

# %%
code_name_lookup = make_code_name_lookup()
code_nut_lookup = get_code_nuts_lookup()

# %%
cluster_df = (pd.Series(clust[1])
              .reset_index(name="cluster")
              .assign(geo_name = lambda df: df["index"].map(code_name_lookup))
              .assign(nuts_name = lambda df: df["index"].map(code_nut_lookup))
              .rename(columns={"index":"geo_code"}))

# %% [markdown]
# ## Explore cluster results

# %% [markdown]
# ### Regional differences

# %%
clust_region_shares = (cluster_df
                       .groupby("cluster")
                       ["nuts_name"]
                       .apply(lambda x: x.value_counts(normalize=True))
                       .unstack()
                       .fillna(0)
                       .stack()
                       .reset_index(name="share")
                       .rename(columns={"level_1":"region"})
                      )
reg_bar = (alt.Chart(clust_region_shares)
           .mark_bar()
           .encode(y="cluster:O",
                   x="share",
                   color="region"))
reg_bar

# %% [markdown]
# ### EFSYP performance differences

# %%
clust_lu = cluster_df.set_index("geo_code")["cluster"].to_dict()

# %%
ey_bench = (ey
            .assign(cluster=lambda df: df["new_la_code"].map(clust_lu))
           .dropna(axis=0,subset=["cluster"]))

# %%
ey_comp = (ey
           .query("year==2019")
           .query("gender=='Total'")
           .assign(cluster=lambda df: df["new_la_code"].map(clust_lu))
           .dropna(axis=0,subset=["cluster"]))

# %%
plot_early_y_perf(ey_bench,2019,"Total")

# %%
plot_early_y_perf(ey_bench,2019,"Boys")

# %% [markdown]
# ### Evolution of differences

# %%
plot_ey_trend(ey_bench)

# %% [markdown]
# ### Year on year comparisons

# %%
plot_ey_year_comp(ey_bench)

# %%
(ey_bench
 .query("gender=='Total'")
 .groupby("indicator").apply(lambda x: x
                             .pivot_table(index="new_la_code",columns="year",values="zscore")
                             .corr())[2019]
 .unstack())


# %% [markdown]
# ### Differences between clusters

# %%
def phf_for_analysis(ph_table, cluster_lookup, code_name_lookup):
    return (phf
            .stack()
            .reset_index(name="score")
            .assign(cluster=lambda df: df["area_code"].map(cluster_lookup))
            .assign(area_name = lambda df: df["area_code"].map(code_name_lookup)))

def calc_mean_ph(ph_long):
    return (pd.concat([ph_long
                     .rename(columns={"score":name})
                     .groupby(["cluster","indicator_name_expanded"])[name].apply(lambda x: function(x)) for 
                     function,name in zip([np.mean, np.std],["mean","std"])],axis=1)
           .reset_index()
           .assign(rank = lambda df: df["indicator_name_expanded"]
                   .map(ph_mean
                        .groupby("indicator_name_expanded")["mean"]
                        .std().rank(ascending=True))))
def phf_ttest(phf_long, sig_level=0.05, equal_var=True):
    """
    """
    
    test_results = []

    for ind in phf_long["indicator_name_expanded"].unique():

        ind_df = (phf_long
                  .query(f"indicator_name_expanded == '{ind}'")
                  .reset_index(drop=True))

        for cl in ind_df["cluster"].unique():

            ttest = ttest_ind(ind_df.query(f"cluster=={cl}")["score"],
                              ind_df.query(f"cluster!={cl}")["score"], equal_var=equal_var)

            test_results.append([ind,cl,ttest.pvalue])

    return (pd.DataFrame(test_results,columns=["indicator","cluster","ttest_sign"])
                .assign(is_sig = lambda df: df["ttest_sign"]<sig_level))
        

def plot_phf_differences(phf_long, sig_level=0.05, equal_var=True):
    
    return (alt.Chart(pipe(phf_long,calc_mean_ph)
                      .merge(phf_ttest(phf_long,sig_level,equal_var),
                             left_on=["indicator_name_expanded","cluster"],right_on=["indicator","cluster"])
                      .query("is_sig == True"))
            .mark_rect(filled=True)
            .encode(x=alt.X("indicator_name_expanded",sort=alt.EncodingSortField("rank",order="descending"),
                            axis=alt.Axis(labels=False,ticks=False)),
                    y="cluster:N",
                    color=alt.Color("mean",scale=alt.Scale(scheme="Redblue", reverse=True)),
                    tooltip=["cluster","indicator_name_expanded","mean"])
            .properties(width=800,height=300))
    


# %%
phf_long = phf_for_analysis(phf,clust_lu, code_name_lookup)

# %%
plot_phf_differences(phf_long, sig_level=0.05)

# %% [markdown]
# ### Improvements in performance inside clusters

# %%
# Where have we seen the greatest improvements inside clusters?

# %%
plot_ey_evol(ey_bench,"Girls")

# %%
