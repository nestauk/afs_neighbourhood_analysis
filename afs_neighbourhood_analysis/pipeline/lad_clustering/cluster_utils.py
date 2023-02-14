import re
import logging
from collections import Counter
from itertools import product, combinations

import networkx as nx
import numpy as np
import pandas as pd
from community import community_louvain
from sklearn.cluster import AffinityPropagation, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture
from toolz import pipe
from umap import UMAP


# %%
def parse_phf(phf_table):
    """Creates new variables depending on categorical information"""

    return (
        phf_table.assign(
            indicator_name_expanded=lambda df: [
                name + "-" + sex for name, sex in zip(df["indicator_name"], df["sex"])
            ]
        )
        .assign(
            indicator_name_expanded=lambda df: [
                name + "-" + category if pd.isnull(category) is False else name
                for name, category in zip(df["indicator_name_expanded"], df["category"])
            ]
        )
        .assign(
            indicator_name_expanded=lambda df: [
                name + "-" + str(category) if pd.isnull(category) is False else name
                for name, category in zip(df["indicator_name_expanded"], df["age"])
            ]
        )
        .assign(
            indicator_name_expanded=lambda df: [
                re.sub("'", "", name) for name in df["indicator_name_expanded"]
            ]
        )
    )


clustering_params = [
    [KMeans, ["n_clusters", range(20, 50, 3)]],
    [AffinityPropagation, ["damping", np.arange(0.5, 0.91, 0.1)]],
    [GaussianMixture, ["n_components", range(20, 50, 5)]],
]
search_params = product(range(5, 55, 5), np.arange(0.4, 1.1, 0.1))


def clustering_consequential_pipe(
    lad_vector: pd.DataFrame,
    pca: int,
    comm_resolution: float,
    efsyp_indicator: pd.DataFrame,
    clustering_options,
):
    """Pipeline that calculates variance in EYFSP for clusters across different
    datasets and parameter values
    """

    umap_df, cluster_lookup = extract_clusters(
        lad_vector, pca, comm_resolution, clustering_options
    )

    # Calculate silhouette scores
    het = calculate_cluster_heterogeneity(efsyp_indicator, cluster_lookup)

    return {
        "pca": pca,
        "comm_resolution": comm_resolution,
        "num_clusters": len(set(cluster_lookup.values())),
        "sil": het,
    }


def extract_clusters(
    lad_vector: pd.DataFrame, pca: int, comm_resolution: float, clustering_options: dict
):
    """Function to extract cluster lookups and positions"""
    lad_reduced = reduce_dim(lad_vector, n_components_pca=pca)
    clustering, indices = build_cluster_graph(lad_reduced, clustering_options)
    lad_cluster_lookup = extract_communities(clustering, comm_resolution, indices)

    umap_df = lad_reduced.assign(
        la_cluster=lambda df: df.index.map(lad_cluster_lookup)
    ).reset_index(drop=False)

    return umap_df, lad_cluster_lookup


def calculate_cluster_heterogeneity(secondary, clusters, gender="Total"):
    """Calculates the silouhette score and variance for secondary indicators
    based on clusters
    """

    second_long = (
        secondary.query("gender == 'Total'")
        .pivot_table(index="new_la_code", columns="indicator", values="zscore")
        .dropna(axis=0)
    )

    second_w_clusters = second_long.assign(
        cluster=lambda df: df.index.map(clusters)
    ).dropna(axis=0)

    sil_sec = silhouette_score(
        second_w_clusters[second_long.columns], second_w_clusters["cluster"]
    )

    intra_cluster_variance = (
        second_w_clusters.reset_index(drop=False)
        .melt(id_vars=["cluster", "new_la_code"])
        .groupby("indicator")
        .apply(lambda df: df.groupby("cluster")["value"].mean().var())
    )

    return sil_sec, intra_cluster_variance


def reduce_dim(
    lad_vector: pd.DataFrame, n_components_pca: int = 50, n_components_umap: int = 2
) -> pd.DataFrame:
    """Reduce dimensionality of sectoral distribution first via PCA and then via UMAP"""

    pca = PCA(n_components=n_components_pca)

    return pipe(
        lad_vector,
        lambda df: pd.DataFrame(pca.fit_transform(lad_vector), index=lad_vector.index),
        lambda df: pd.DataFrame(
            UMAP(n_components=n_components_umap).fit_transform(df),
            index=df.index,
            columns=["x", "y"],
        ),
    )


def build_cluster_graph(
    vectors: pd.DataFrame,
    clustering_algorithms: list,
    n_runs: int = 10,
    sample: int = None,
):
    """Builds a cluster network based on observation co-occurrences
    in a clustering output

    Args:
        vectors: vectors to cluster
        clustering_algorithms: a list where the first element is the clustering
            algorithm and the second element are the parameter names and sets
        n_runs: number of times to run a clustering algorithm
        sample: size of the vector to sample.

    Returns:
        A network where the nodes are observations and their edges number
            of co-occurrences in the clustering

    #FIXUP: remove the nested loops
    """

    clustering_edges = []

    index_to_id_lookup = {n: ind for n, ind in enumerate(vectors.index)}

    logging.info("Running cluster ensemble")
    for cl in clustering_algorithms:

        logging.info(cl[0])

        algo = cl[0]

        parametres = [{cl[1][0]: v} for v in cl[1][1]]

        for par in parametres:

            logging.info(f"running {par}")

            for _ in range(n_runs):

                cl_assignments = algo(**par).fit_predict(vectors)
                index_cluster_pair = {n: c for n, c in enumerate(cl_assignments)}

                indices = range(0, len(cl_assignments))

                pairs = combinations(indices, 2)

                for p in pairs:

                    if index_cluster_pair[p[0]] == index_cluster_pair[p[1]]:
                        clustering_edges.append(frozenset(p))

    edges_weighted = Counter(clustering_edges)

    logging.info("Building cluster graph")

    edge_list = [(list(fs)[0], list(fs)[1]) for fs in edges_weighted.keys()]
    cluster_graph = nx.Graph()
    cluster_graph.add_edges_from(edge_list)

    for ed in cluster_graph.edges():

        cluster_graph[ed[0]][ed[1]]["weight"] = edges_weighted[
            frozenset([ed[0], ed[1]])
        ]

    return cluster_graph, index_to_id_lookup


def extract_communities(
    cluster_graph: nx.Graph, resolution: float, index_lookup: dict
) -> list:
    """Extracts community from the cluster graph and names them

    Args:
        cluster_graph: network object
        resolution: resolution for community detection
        index_lookup: lookup between integer indices and project ids

    Returns:
        a lookup between communities and the projects that belong to them
    """
    logging.info("Extracting communities")
    comms = community_louvain.best_partition(cluster_graph, resolution=resolution)

    comm_assignments = {
        comm: [index_lookup[k] for k, v in comms.items() if v == comm]
        for comm in set(comms.values())
    }

    return {
        lad: cluster
        for cluster, lad_list in comm_assignments.items()
        for lad in lad_list
    }
