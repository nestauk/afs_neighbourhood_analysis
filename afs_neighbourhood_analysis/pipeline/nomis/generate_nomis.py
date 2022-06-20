import pandas as pd
import glob
import pandas as pd
from dateutil.parser import parse
from functools import reduce

from afs_neighbourhood_analysis import PROJECT_DIR
from afs_neighbourhood_analysis.pipeline.nomis.nomis_utils import (
    get_rename_variable_name,
    get_value,
    rename_geocode,
    aggregate_values,
    get_year,
    get_columns,
    concat_indicators,
)

from afs_neighbourhood_analysis.getters.get_nomis import get_nomis


def create_nomis():
    """
    Fetch all tables for an indicator
    """

    get_nomis()
    print("Generating NOMIS indicators...")
    data = {}
    for filename in glob.glob(f"{PROJECT_DIR}/inputs/data/raw/nomis/*.csv"):
        f = filename.replace(f"{PROJECT_DIR}/inputs/data/raw/nomis/", "")
        data[f[:-4]] = pd.read_csv(filename, sep=",")

    funcs = [
        get_rename_variable_name,
        get_value,
        rename_geocode,
        aggregate_values,
        get_year,
        get_columns,
        concat_indicators,
    ]

    result = reduce(lambda res, f: f(res), funcs, data)
    print("DONE")
    print(result)
    return result


if __name__ == "__main__":
    """
    Creates nomis indicators dataframe and saves in directory, locally.
    """
    indicators = create_nomis()
    indicators.to_csv(f"{PROJECT_DIR}/outputs/nomis_indictors.csv", sep=",")
