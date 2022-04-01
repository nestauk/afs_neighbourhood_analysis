import re

import pandas as pd


def clean_fingertips_table(table: pd.DataFrame) -> pd.DataFrame:
    """Cleans up a fingertips table"""

    table.columns = [re.sub(" ", "_", col).lower() for col in table.columns]
    return table
