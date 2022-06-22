import pandas as pd
from datetime import datetime

VARIABLE_NAME_DICT = {
    "nomis_ashe_earnings_resident_analysis": "Average annual gross pay of residents",
    "nomis_aps_dependant_children_lone_parent_household_rate": "Percentage of lone parent households with dependant children",
    "nomis_aps_dependant_children_household_rate": "Percentage of households with dependant children",
    "nomis_jobseekers_allowance": "Total number of jobseekers claiming jobseekers allowance",
}


def add_data_source(data_dict):
    """
    Create column indicating the data source.

        Parameters:
            data_dict (dict): A dictionary of filenames (keys) and dataframes (values)

        Returns:
            data_dict (dict): A dictionary of filenames (keys) and dataframes with new column (values)
    """
    for key, dataset in data_dict.items():
        dataset["source"] = key.split("_")[1].upper()
        data_dict[key] = dataset

    return data_dict


def get_rename_variable_name(data_dict):
    """
    This function goes through a dictionary of file names (keys) and datasets (values) and finds the column with the indicator name. It then renames that column name to "indictor name".
    If a dataset has multiple indicator names in one column, this is treated as individual indicators - a subset of the dataset if created for each unique indictor in the dataset.
    Additionally, for the cases where there is no indictor name, `variable_name_dict` is used to map a indicator name (in the `else` portion of the loop)

        Parameters:
            data_dict (dict): A dictionary of filenames (keys) and dataframes (values)

        Returns:
            data_dict (dict): A dictionary of filenames (keys) and a corresponding list of dataframes (values)
    """

    for key, dataset in data_dict.items():

        if key in ["nomis_claimant_count", "nomis_ra_household_income_per_head"]:
            dataset.rename(columns={"MEASURE_NAME": "indicator_name"}, inplace=True)
            df_list = [dataset]
            data_dict[key] = df_list

        elif ("PAY_NAME" in dataset.columns) and (
            key == "nomis_ashe_earnings_resident_analysis"
        ):
            dataset.rename(columns={"PAY_NAME": "indicator_name"}, inplace=True)
            dataset["indicator_name"] = VARIABLE_NAME_DICT[key]
            df_list = [dataset]
            data_dict[key] = df_list

        elif "CELL_NAME" in dataset.columns:
            dataset.rename(columns={"CELL_NAME": "indicator_name"}, inplace=True)
            df_list = [dataset]
            data_dict[key] = df_list

        elif ("INDUSTRY_NAME" and "MEASURE_NAME") in dataset.columns:
            dataset["INDUSTRY_NAME"] = (
                "Industry percentage - " + dataset["INDUSTRY_NAME"]
            )
            df_list = [y for x, y in dataset.groupby("INDUSTRY_NAME", as_index=False)]
            df_list = [
                df.rename(columns={"INDUSTRY_NAME": "indicator_name"}) for df in df_list
            ]
            data_dict[key] = df_list

        elif "VARIABLE_NAME" in dataset.columns:
            if len(dataset["VARIABLE_NAME"].unique()) > 1:
                df_list = [
                    y for x, y in dataset.groupby("VARIABLE_NAME", as_index=False)
                ]
                df_list = [
                    df.rename(columns={"VARIABLE_NAME": "indicator_name"})
                    for df in df_list
                ]
                data_dict[key] = df_list
            else:
                dataset.rename(
                    columns={"VARIABLE_NAME": "indicator_name"}, inplace=True
                )
                df_list = [dataset]
                data_dict[key] = df_list
        else:
            for i in VARIABLE_NAME_DICT.keys():
                if i in key.lower():
                    dataset["indicator_name"] = VARIABLE_NAME_DICT[i]
                    df_list = [dataset]
                    data_dict[key] = df_list

    return data_dict


def get_value(data_dict_w_list):
    """
    Create value column for each indicator from dictionary of file names (key) and list of dataframes (values)

        Parameters:
            data_dict_w_list (dict): A dictionary of filenames (keys) and a corresponding list of dataframes (values)

        Returns:
            data_dict_w_list (dict): A dictionary of filenames (keys) and a corresponding list of dataframes (values)
    """

    for key, dataset_list in data_dict_w_list.items():
        df_list = []
        for dataset in dataset_list:
            if ("MEASURES_NAME" in dataset.columns) and (
                dataset["MEASURES_NAME"].str.contains("Variable").sum() > 0
            ):
                dataset["value"] = dataset.loc[
                    dataset["MEASURES_NAME"] == "Variable", "OBS_VALUE"
                ]
                dataset.dropna(subset=["value"], inplace=True)
                df_list.append(dataset)

            elif ("MEASURES_NAME" in dataset.columns) and (
                dataset["MEASURES_NAME"].str.contains("Value").sum() > 0
            ):
                dataset["value"] = dataset.loc[
                    dataset["MEASURES_NAME"] == "Value", "OBS_VALUE"
                ]
                dataset.dropna(subset=["value"], inplace=True)
                df_list.append(dataset)
            else:
                dataset.rename(columns={"OBS_VALUE": "value"}, inplace=True)
                df_list.append(dataset)
        data_dict_w_list[key] = df_list

    return data_dict_w_list


def rename_geocode(data_dict_w_list):
    """
    Create geocode column for each indicator from dictionary of file names (key) and list of dataframes (values)

        Parameters:
            data_dict_w_list (dict): A dictionary of filenames (keys) and a corresponding list of dataframes (values)

        Returns:
            data_dict_w_list (dict): A dictionary of filenames (keys) and a corresponding list of dataframes (values)
    """
    for key, dataset_list in data_dict_w_list.items():
        df_list = []
        for dataset in dataset_list:
            dataset.rename(
                columns={
                    "GEOGRAPHY_CODE": "area_code",
                    "GEOGRAPHY_NAME": "area_name",
                    "GEOGRAPHY_TYPE": "area_type",
                },
                inplace=True,
            )
            dataset = dataset[dataset["area_code"].str.startswith("E")].reset_index(
                drop=True
            )
            df_list.append(dataset)
        data_dict_w_list[key] = df_list

    return data_dict_w_list


def validate_date(date):
    """
    Check whether DATE_CODE value is in the right format.

        Parameters:
            date (str): A string of a date

        Returns:
            date (datetime): Datetime string
            or
            date (str): A string of year
    """
    try:
        return datetime.strptime(date, "%Y-%m").year
    except:
        return date


def get_year(data_dict_w_list):
    """
    Changes date format yyyy-mm to yyyy for every value (else, only takes the year)

        Parameters:
            data_dict_w_list (dict): A dictionary of filenames (keys) and a corresponding list of dataframes (values)

        Returns:
            data_dict_w_list (dict): A dictionary of filenames (keys) and a corresponding list of dataframes (values)
    """
    for key, dataset_list in data_dict_w_list.items():
        df_list = []
        for dataset in dataset_list:
            dataset["year"] = dataset["DATE_CODE"].apply(lambda x: validate_date(x))
            df_list.append(dataset)
        data_dict_w_list[key] = df_list

    return data_dict_w_list


def get_columns(data_dict_w_list):
    """
    Selects columns of interest for dataset

        Parameters:
            data_dict_w_list (dict): A dictionary of filenames (keys) and a corresponding list of dataframes (values)

        Returns:
            data_dict_w_list (dict): A dictionary of filenames (keys) and a corresponding list of dataframes (values)
    """
    for key, dataset_list in data_dict_w_list.items():
        df_list = []
        for dataset in dataset_list:

            dataset["indicator_name_expanded"] = dataset["indicator_name"]
            dataset = dataset.dropna(subset=["value"])
            dataset = dataset[
                [
                    "year",
                    "area_name",
                    "area_code",
                    "indicator_name",
                    "value",
                    "indicator_name_expanded",
                    "source",
                ]
            ].reset_index(drop=True)
            df_list.append(dataset)
        data_dict_w_list[key] = df_list
    return data_dict_w_list


def concat_indicators(data_dict_w_list):
    """
    Concatenate all NOMIS indicators

        Parameters:
            data_dict_w_list (dict): A dictionary of filenames (keys) and a corresponding list of dataframes (values)

        Returns:
            final_indicators (pandas.DataFrame): A dataframe
    """
    data_list_full = []
    for key, dataset in data_dict_w_list.items():
        data_list_full.extend(dataset)
    final_indicators = pd.concat(data_list_full).reset_index(drop=True)

    return final_indicators
