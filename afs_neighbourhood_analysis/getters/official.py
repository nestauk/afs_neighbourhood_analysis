import json
import logging
import os
from typing import Union, List

import pandas as pd

from afs_neighbourhood_analysis import PROJECT_DIR
from afs_neighbourhood_analysis.utils.metaflow import get_run


def public_health_indicators() -> pd.DataFrame:
    """Fetch public health indicators"""

    return pd.concat(
        [
            table
            for table in get_run(
                "PublicHealthIndicators"
            ).data.indicator_tables.values()
        ]
    ).reset_index(drop=False)


def fetch_indicators(frameworks: Union[List, str] = "all") -> pd.DataFrame:
    """Fetch indicators based on their framework.

    Args:
        frameworks: if all, gets all indicators. Otherwise, a list
    """

    if frameworks == "all":
        return pd.concat(
            [
                pd.concat([t.assign(framework=frame) for t in tables])
                for frame, tables in get_run(
                    "HealthIndicators"
                ).data.framework_tables.items()
                if len(tables) > 0
            ]
        ).reset_index(drop=False)
    else:
        # return pd.concat(
        #     [
        #         [pd.concat(t.assign(framework=frame)) for t in tables]
        #         for frame, tables in get_run(
        #             "HealthIndicators"
        #         ).data.framework_tables.items()
        #         if frame in frameworks
        #     ]
        # ).reset_index(drop=False)

        return pd.concat(
            [
                pd.concat([t.assign(frame=f) for t in tables])
                for f, tables in get_run(
                    "HealthIndicators"
                ).data.framework_tables.items()
                if (f in frameworks) & (len(tables) > 0)
            ]
        )


def area_name_lookup() -> dict:

    lookup_dir = f"{PROJECT_DIR}/inputs/data/la_name_lookup.json"

    if os.path.exists(lookup_dir) is False:
        logging.info("making lookup")

        lookup = (
            public_health_indicators()
            .drop_duplicates(subset=["area_code"])
            .set_index("area_code")["area_name"]
            .to_dict()
        )

        with open(lookup_dir, "w") as outfile:
            json.dump(lookup, outfile)

        return lookup

    else:

        with open(lookup_dir, "r") as infile:
            return json.load(infile)


# def framework_name_lookup() ->:
#     """Read the
#     """
