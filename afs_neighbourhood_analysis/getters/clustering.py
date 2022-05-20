# Getters for clustering outputs etc

import pickle

import pandas as pd
from toolz import pipe

from afs_neighbourhood_analysis import PROJECT_DIR


def parse_clustering_diagnostics(clustering_result: dict) -> pd.Series:
    """Parses clustering diagnostics"""

    out_dict = {
        k: v
        for k, v in clustering_result.items()
        if k in ["pca", "comm_resolution", "num_clusters"]
    }
    out_dict["silouhette"] = clustering_result["sil"][0]
    var_dict = pipe(
        clustering_result["sil"][1],
        dict,
        lambda _dict: {k.split("_")[0] + "_variance": v for k, v in _dict.items()},
    )

    return pd.Series({**out_dict, **var_dict})


def clustering_diagnostics() -> pd.DataFrame:
    """Reads clustering diagnostics.
    Contents:
        pca: number of dimensions used in PCA
        comm_resolution: resolution for community extraction
        num_clusters: number of clusters extracted
        diagnostic_var: diagnostic variable. It can be...
            silouhette score for clustering outputs v early year outputs
            _variance: variance in scores for various early year scores
            including average point score, % with acceptable
            communication, language and literature and early year goals,
            and % with good level of development.
        value: score for the diagnostic variable
    """

    with open(
        f"{PROJECT_DIR}/inputs/data/cluster_grid_search_results.p", "rb"
    ) as infile:
        results = pickle.load(infile)

    return pd.DataFrame([parse_clustering_diagnostics(r) for r in results]).melt(
        id_vars=["pca", "comm_resolution", "num_clusters"],
        var_name="diagnostic_var",
    )
