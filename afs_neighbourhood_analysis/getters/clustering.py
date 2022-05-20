# Getters for clustering outputs etc

import pickle
from functools import partial

import pandas as pd
from toolz import pipe

from afs_neighbourhood_analysis import PROJECT_DIR
from afs_neighbourhood_analysis.analysis.feature_selection_scratch import (
    el_goals,
    public_health_framework,
    remove_missing,
)

from afs_neighbourhood_analysis.pipeline.lad_clustering.cluster_utils import (
    clustering_consequential_pipe,
    parse_phf,
)

from afs_neighbourhood_analysis.pipeline.lad_clustering.conseq_clustering import (
    most_recent_data,
    standardise_early_years,
)


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


def early_years_for_clustering() -> pd.DataFrame:
    """Reads a standardised version of the early years data"""

    return pipe(el_goals(), standardise_early_years)


def public_health_for_clustering() -> pd.DataFrame:
    """Reads a processed version of the public health framework data"""

    return pipe(
        public_health_framework(),
        parse_phf,
        most_recent_data,
        partial(remove_missing, index_name="indicator_name_expanded"),
    )
