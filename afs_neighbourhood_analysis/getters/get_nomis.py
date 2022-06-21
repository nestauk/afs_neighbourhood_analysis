import pandas as pd


def nomis_indicators():
    """
    Fetch final processed NOMIS indicators
    """
    return pd.read_csv(f"{PROJECT_DIR}/outputs/nomis_indicators.csv")
