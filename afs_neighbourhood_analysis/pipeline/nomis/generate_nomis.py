import logging
import pandas as pd
import glob
import os
import pandas as pd
from dateutil.parser import parse
from functools import reduce
from afs_neighbourhood_analysis import PROJECT_DIR
from afs_neighbourhood_analysis.pipeline.nomis.nomis_utils import (
    add_data_source,
    get_rename_variable_name,
    get_value,
    rename_geocode,
    get_year,
    get_columns,
    concat_indicators,
)
from afs_neighbourhood_analysis.pipeline.nomis.fetch_nomis import fetch_nomis

logger = logging.getLogger(__name__)


def create_nomis():
    """
    Fetch all tables for an indicator
    """

    if not os.path.exists(f"{PROJECT_DIR}/inputs/data/raw/nomis/"):
        os.makedirs(f"{PROJECT_DIR}/inputs/data/raw/nomis/")

    logger.info("Fetching raw NOMIS indicators...")
    fetch_nomis()

    logger.info("Generating NOMIS indicators...")
    data = {}
    for filename in glob.glob(f"{PROJECT_DIR}/inputs/data/raw/nomis/*.csv"):
        f = filename.replace(f"{PROJECT_DIR}/inputs/data/raw/nomis/", "")
        data[f[:-4]] = pd.read_csv(filename, sep=",")

    funcs = [
        add_data_source,
        get_rename_variable_name,
        get_value,
        rename_geocode,
        get_year,
        get_columns,
        concat_indicators,
    ]

    result = reduce(lambda res, f: f(res), funcs, data)

    logger.info(result)
    logger.info("DONE")

    return result


if __name__ == "__main__":
    """
    Creates nomis indicators dataframe and saves in directory, locally.
    """
    indicators = create_nomis()
    indicators.to_csv(
        f"{PROJECT_DIR}/outputs/nomis_indicators.csv", sep=",", index=False
    )
