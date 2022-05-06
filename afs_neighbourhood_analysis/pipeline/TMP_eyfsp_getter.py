import pandas as pd
import numpy as np
from afs_neighbourhood_analysis import PROJECT_DIR

input_fpath = f"{PROJECT_DIR}/outputs"


def get_edu_dataframes():
    """
    TEMPORARY getter for retrieving the csv files from afs_neighbourhood_analysis/outputs and converting them into cleaned pd.DataFrames. Stored in a dictionary of dataframes.

    Outputs:
        Dictionary of pd.DataFrames with the following keys -
        ELG_GLD = DataFrame containing the numbers and percentages of Early Learning Goals and Good Levels of Development for national, regional and unitary authority, separated by gender. Spans the years 2013-2019.
        AoL= Areas of Learning DataFrame separated by gender, geography (national, regional and unitary authority), at least expected percentage and number, exceeded percentage and number. Spans the years 2013-2019.
        ELG = Each Early Learning Goal category separated by gender, geography (national, regional and unitary authority), at least expected percentage and number, exceeded percentage and number. Spans the years 2013-2019.
        ELG_GLD_add = DataFrame containing the same as ELG_GLD but separated additionally by characteristic: ethnicity, FSM, SEND and First language. Spans the years 2013-2019.
        COM_LIT_MAT = Dataframe containing the number and percentages of children getting the "at least expected" level in the EYFSP categories of Communication and Language, Literacy and Maths, broked down by gender, FSM status and geography (national, regional, unitary authority). Spans the years 2013-2019.
        ELG_GLD_LAD = DataFrame containing number and percentages of children for the Early Learning Goals and reaching a Good Level of Development, broken down by region and Local Authority District. Spans the years 2014-2019.

    """

    keys = ["ELG_GLD", "AoL", "ELG", "ELG_GLD_add", "COM_LIT_MAT", "ELG_GLD_LAD"]

    filenames = [
        f"{input_fpath}/APS_GLD_ELG_EXP_2013_2019.csv",
        f"{input_fpath}/AREAS_OF_LEARNING_2013_2019.csv",
        f"{input_fpath}/ELG_2013_2019.csv",
        f"{input_fpath}/EYFSP_LA_1_key_measures_additional_tables_2013_2019.xlsx",
        f"{input_fpath}/EYFSP_LA_2_com_lit_maths_additional_tables_2013_2019.xlsx",
        f"{input_fpath}/EYFSP_LAD_pr_additional_tables_2014_2019.xlsx",
    ]

    edu_dataframes = {}

    for key, file in zip(keys, filenames):
        if ".csv" in file:
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file, engine="openpyxl")
        df.replace(".", np.nan, inplace=True)
        edu_dataframes[key] = df

    return edu_dataframes
