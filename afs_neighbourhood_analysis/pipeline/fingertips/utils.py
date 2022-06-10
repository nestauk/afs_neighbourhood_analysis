import logging
import re
from urllib3.exceptions import HTTPError

import pandas as pd
from pandas.errors import ParserError
from fingertips_py import get_data_for_indicator_at_all_available_geographies


def clean_fingertips_table(table: pd.DataFrame) -> pd.DataFrame:
    """Cleans up variables fingertips table"""

    if type(table) == pd.DataFrame:
        table.columns = [re.sub(" ", "_", col).lower() for col in table.columns]
        return table
    else:
        pass


def robust_fetch_table(indicator_id: int, verbose: bool = False):
    """Tries to fetch an indicator robustly"""

    if verbose:
        print(indicator_id)
    try:
        return get_data_for_indicator_at_all_available_geographies(indicator_id)

    except HTTPError:
        logging.info(f"{indicator_id} http error")

    except ParserError:
        logging.info(f"{indicator_id} pandas parsing error")
