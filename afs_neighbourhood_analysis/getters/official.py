import json
import logging
import os

import pandas as pd
from toolz import pipe
from fingertips_py import (
    get_all_profiles,
    get_metadata_for_profile_as_dataframe,
    get_all_areas_for_all_indicators,
)

from afs_neighbourhood_analysis import PROJECT_DIR
from afs_neighbourhood_analysis.pipeline.fingertips.utils import clean_fingertips_table
from afs_neighbourhood_analysis.utils.metaflow import get_run


DISTRICT_IDS = set([101, 301, 401])


def fetch_indicator_table(profile_id: int) -> pd.DataFrame:
    """Fetch indicators based on their profile.

    Args:
        profile_id: what profile to fetch
    """

    return get_run("ParseIndicators").data.framework_clean_dfs[profile_id]


def area_name_lookup() -> dict:
    """Lookup between area names and codes"""

    lookup_dir = f"{PROJECT_DIR}/inputs/data/la_name_lookup.json"

    # It checks if it needs to make the lookup first time around
    if os.path.exists(lookup_dir) is False:
        logging.info("making lookup")

        lookup = (
            fetch_indicator_table(19)
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


def profile_name_lookup() -> dict:
    """Lookup between frameworks and names"""

    return {
        profile_dict["Id"]: profile_dict["Name"] for profile_dict in get_all_profiles()
    }


def indicator_inventory() -> pd.DataFrame:
    """Table with metadata for all indicators
    available for each profile which are available at the local authority district level

    """

    # We use this to tag indicators with their profile
    profile_name = profile_name_lookup()

    # This gets indicators which are availabel at the district level
    district_ind_ids = pipe(
        get_all_areas_for_all_indicators(),
        lambda df: df.loc[df["AreaTypeId"].isin(DISTRICT_IDS)]["IndicatorId"],
        set,
    )

    return pipe(
        pd.concat(
            [
                (
                    get_metadata_for_profile_as_dataframe(profile["Id"])
                    .assign(profile=profile["Id"])
                    .assign(profile_name=lambda df: df["profile"].map(profile_name))
                )
                for profile in get_all_profiles()
            ]
        ),
        lambda df: (
            df.loc[df["Indicator ID"].isin(district_ind_ids)].reset_index(drop=True)
        ),
        clean_fingertips_table,
    )
