from io import StringIO
import requests
import os
import logging

import ratelim
from datetime import date
from pandas import concat, read_csv
import afs_neighbourhood_analysis

from pathlib import Path

logger = logging.getLogger(__name__)
CELL_LIMIT = 25_000
REQUESTS_PER_SECOND = 2


def make_nomis(geo_type, year_l, project_dir=None):
    """Make NOMIS Labour Market Survey, BRES datasets
    Args:
        geo_type (str): Geography type to consider.
            Options: 'cau' (county and unitary authorities).
        year_l (list[int]): Year of data to consider
        project_dir (str): Project path
    """

    if project_dir is None:
        project_dir = afs_neighbourhood_analysis.PROJECT_DIR
        if not os.path.exists(f"{project_dir}/inputs/data/raw/nomis/"):
            os.makedirs(f"{project_dir}/inputs/data/raw/nomis/")

        # Path(f"{project_dir}/inputs/data/raw/nomis").mkdir(parents=False, exist_ok=True)
        # Path(f"{project_dir}/inputs/data/interim/nomis/").mkdir(parents=False, exist_ok=True)

    for dataset in ["UNEMPLOYMENT_RATE", "BRES_INDUSTRY", "QUALIFICATION_DEGREE"]:

        raw_fout = f"{project_dir}/inputs/data/raw/nomis/nomis_{dataset}_{geo_type}.csv"
        tidy_fout = (
            f"{project_dir}/inputs/data/interim/nomis/nomis_{dataset}_{geo_type}.csv"
        )

        # Fetch and save raw data if not present
        if os.path.exists(raw_fout):
            df = read_csv(raw_fout)
        else:
            df = get_nomis(dataset, geo_type, year_l)
            df.to_csv(raw_fout, index=False)


def get_nomis(dataset, geo_type, year_list):
    """Get NOMIS Labour Market Survey, BRES datasets from NOMIS for given year and geography
    Args:
        dataset (str, {'BRES'}): BRES
        geo_type (str, {'cau'}): Geography type.
            'cau', or geography type to be passed straight to the API query.
            For example `TYPE431` will give local authorities: county / unitary (as of April 2021).
        year (int): Year
    Returns:
        pandas.DataFrame
    Notes:
        NOMIS data-set ID's:
            17_5: labour market survey (Unemployment Rate 16+)
            189_1: Business Register and Employment Survey :
                    open access (2015 to 2020)
    """
    logger.info(f"Fetching {dataset} for {geo_type}")

    if dataset == "UNEMPLOYMENT_RATE":
        data_id = 17
        tail_id = 5
        API_cols = "&variable=83&measures=20599,21001,21002,21003"

    elif dataset == "QUALIFICATION_DEGREE":
        data_id = 17
        tail_id = 5
        API_cols = "&variable=1126&measures=20599,21001,21002,21003"

    elif dataset == "BRES_INDUSTRY":
        data_id = 189
        tail_id = 1
        API_cols = "&industry=150994945...150994965&employment_status=1&measure=2&measures=20100"

    API_start = (
        f"http://www.nomisweb.co.uk/api/v01/dataset/NM_{data_id}_{tail_id}.data.csv"
    )

    if geo_type == "cau":
        API_geo = "?geography=TYPE431"
    else:
        print(geo_type)
        raise ValueError(f"`geo_type` value {geo_type} not valid")

    API_year = "&date="
    years = []
    for year in year_list:
        years.append(f"{year}-12")
    API_year = API_year + ",".join(years)

    if dataset == "ECON_ACTIVE_STEM_PRO":
        fields = [
            "date",
            "date_name",
            "date_code",
            "geography_type",
            "geography_code",
            "measures_name",
            "variable",
            "cell_name",
            "obs_value",
            "obs_status_name",
            "obs_status",
            "record_count",
        ]

    else:
        fields = [
            "date",
            "date_name",
            "date_code",
            "geography_type",
            "geography_code",
            "measures_name",
            "variable",
            "variable_name",
            "obs_value",
            "obs_status_name",
            "obs_status",
            "record_count",
        ]

    API_select = f"&select={','.join(fields)}"
    column_map = {"GEOGRAPHY_NAME": "geo_nm", "GEOGRAPHY_CODE": "geo_cd"}

    query = API_start + API_geo + API_year + API_cols + API_select

    return query_nomis(query).rename(columns=column_map)


@ratelim.patient(REQUESTS_PER_SECOND, time_interval=1)
def query_nomis(link, offset_size=CELL_LIMIT):
    """Query NOMIS api with ratelimiting and pagination
    Args:
        link (str): URL of NOMIS API query
        offset_size (int): Size of pagination chunks
    Returns:
        pandas.DataFrame
    """
    logger.info(f"Getting: {link}")

    df_container = []
    offset = 0
    first_page = True
    records_left = 1  # dummy

    # While the final record we will obtain is below the total number of records:
    while records_left > 0:
        # Modify the query link with the offset
        query = link + "&recordoffset={off}".format(off=str(offset))

        response = requests.get(query)

        if response.status_code == 200:

            if response.text == "":
                raise ValueError(f"Empty response for query: {query}")

            # Run query and store
            df_container.append(read_csv(StringIO(response.text)))

            # Update the offset (next time we will query from this point)
            offset += offset_size

            # Get number of records from first iteration
            if first_page:
                total_records = df_container[-1].RECORD_COUNT.values[0]
                logger.info(f"{total_records} to download")
                records_left = total_records
                first_page = False

            records_left -= offset_size
            logger.info(f"{records_left} records left")

        else:
            continue

    # Concatenate all the outputs
    return concat(df_container)


def _check_geo_type_suffix(x):
    """Checks if `geo_type` suffix contains an `int`"""
    try:
        return int(x)
    except:
        raise ValueError(f"`geo_type` suffix: '{x}' cannot be parsed as `int`.")


if __name__ == "__main__":
    years = [i for i in range(2009, date.today().year)]
    geo_type_ = "cau"

    make_nomis(geo_type_, years, None)
