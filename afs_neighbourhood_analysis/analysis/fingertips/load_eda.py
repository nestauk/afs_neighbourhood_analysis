import os

import pandas as pd
from toolz import pipe

from afs_neighbourhood_analysis import PROJECT_DIR


profile_path = f"{PROJECT_DIR}/outputs/reports/data_profiles"

os.makedirs(profile_path, exist_ok=True)


def last_year(period: str):
    """Parses time periods into the last year"""

    if type(period) == int:
        return period

    if "-" in period:
        if "/" in period:
            if "Q" in period:
                return int(
                    f"20{period.split('-')[1].strip().split(' ')[0].split('/')[1]}"
                )
            else:
                return int(f"20{period.split('/')[-1]}")
        elif any(x in period for x in ["Mar", "Jul", "Aug"]):
            return int(period.split(" ")[-1])
        elif "Jul" in period:
            return int(period.split(" ")[-1])
        elif "Q" in period:
            return

        else:
            return int(f"20{period.split('-')[1].strip()}")
    elif " " in period:
        if "Q" in period:
            if "/" in period:
                return int(f"20{period.split(' ')[0].split('/')[1]}")
            else:
                return int(period.split(" ")[0])
        elif "/" in period:
            return int(f"20{period.split('/')[-1]}")

        else:
            return int(period.split(" ")[1])

    elif "/" in period:
        return int(f"20{period.split('/')[-1]}")
    else:
        return int(period)


def parse_public_health(public_health_indicators: pd.DataFrame) -> pd.DataFrame:
    """Parsing of public health indicators"""

    keep_cols = [
        "indicator_id",
        "indicator_name",
        "area_code",
        "area_name",
        "area_type",
        "sex",
        "age",
        "category_type",
        "category",
        "last_year",
        "time_period",
        "value",
    ]

    return public_health_indicators.assign(
        last_year=lambda df: df["time_period"].apply(last_year)
    )[keep_cols]


def keep_districts(public_health_indicators: pd.DataFrame) -> pd.DataFrame:
    """Keeps districts / unitary authorities"""

    return public_health_indicators.loc[
        public_health_indicators["area_type"].apply(lambda x: "Districts" in x)
    ].reset_index(drop=True)


def keep_counties(public_health_indicators: pd.DataFrame) -> pd.DataFrame:
    """Keeps districts / unitary authorities"""

    return public_health_indicators.loc[
        public_health_indicators["area_type"].apply(lambda x: "Counties" in x)
    ].reset_index(drop=True)


def parse_health_indicators(health_indicators: pd.DataFrame) -> pd.DataFrame:
    """Applies the pipeline above to health indicators"""
    return pipe(health_indicators, parse_public_health, keep_counties)
