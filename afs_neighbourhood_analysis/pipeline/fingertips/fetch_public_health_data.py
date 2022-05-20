# Script to fetch and save public health profile data
# This is provisional.

import logging

import pandas as pd
from fingertips_py import get_metadata_for_profile_as_dataframe
from toolz import pipe

from afs_neighbourhood_analysis import PROJECT_DIR
from afs_neighbourhood_analysis.analysis.fingertips.load_eda import (
    parse_health_indicators,
)
from afs_neighbourhood_analysis.pipeline.fingertips.utils import (
    clean_fingertips_table,
    robust_fetch_table,
)


def fetch_profile(profile_id: int, verbose: bool = True) -> pd.DataFrame:
    """Fetch all tables for an indicator"""

    indicator_ids = pipe(
        set(get_metadata_for_profile_as_dataframe(profile_id)["Indicator ID"]), list
    )

    indicator_table = []

    for n, i in enumerate(indicator_ids):
        if verbose:
            if n % 10 == 0:
                logging.info(i)

        t = robust_fetch_table(i)

        if type(t) == pd.DataFrame:
            table = pipe(t, clean_fingertips_table, parse_health_indicators)
            indicator_table.append(table)

    return pd.concat(indicator_table).reset_index(drop=True)


if __name__ == "__main__":

    pipe(
        fetch_profile(19),
        lambda df: df.to_csv(
            f"{PROJECT_DIR}/inputs/data/public_health_profile.csv", index=False
        ),
    )
