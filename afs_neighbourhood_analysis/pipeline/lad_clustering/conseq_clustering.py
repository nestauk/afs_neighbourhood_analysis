import logging
import pickle
from functools import partial

import numpy as np
import pandas as pd
from itertools import product
from toolz import pipe
from scipy.stats import zscore

from afs_neighbourhood_analysis import PROJECT_DIR
from afs_neighbourhood_analysis.analysis.feature_selection_scratch import (
    el_goals,
    public_health_framework,
    remove_missing,
)

from afs_neighbourhood_analysis.pipeline.lad_clustering.cluster_utils import (
    clustering_params,
    clustering_consequential_pipe,
    parse_phf,
)


def most_recent_data(phf: pd.DataFrame) -> pd.DataFrame:
    """Focus on the most recent slice of the data"""
    last_years = phf.groupby("indicator_id")["last_year"].max().to_dict()

    return (
        phf.loc[
            [
                last_years[ind] == year
                for ind, year in zip(phf["indicator_id"], phf["last_year"])
            ]
        ]
        .drop_duplicates(["indicator_name_expanded", "area_code"])
        .reset_index(drop=True)
        .pivot(index="area_code", columns="indicator_name_expanded", values="value")
        .apply(partial(zscore, nan_policy="omit"))
    )


def standardise_early_years(early_years: pd.DataFrame) -> pd.DataFrame:
    """Standardises early years indicators"""

    return (
        early_years.groupby(["year", "gender", "indicator"])
        .apply(
            lambda df: (
                df.assign(zscore=lambda df_2: zscore(df_2["score"], nan_policy="raise"))
            )
        )
        .reset_index(drop=True)
    )


if __name__ == "__main__":

    logging.info("Reading and processing data")
    early_years = pipe(el_goals(), standardise_early_years)

    # This gives a processed version of the public health
    # framework indicators focusing on the most recent years and removing
    # indicators with a high number of missing values

    logging.info(early_years.head())

    public_health_profile = pipe(
        public_health_framework(),
        parse_phf,
        most_recent_data,
        partial(remove_missing, index_name="indicator_name_expanded"),
    )

    logging.info(public_health_profile.head())

    logging.info("Clustering grid search")
    search_params = product(range(5, 90, 15), np.arange(0.4, 1.1, 0.1))

    clustering_results = [
        clustering_consequential_pipe(
            public_health_profile,
            param[0],
            param[1],
            early_years,
            clustering_params,
        )
        for param in search_params
    ]

    with open(
        f"{PROJECT_DIR}/inputs/data/cluster_grid_search_results.p", "wb"
    ) as outfile:
        pickle.dump(clustering_results, outfile)
