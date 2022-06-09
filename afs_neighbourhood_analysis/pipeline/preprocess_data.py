import pandas as pd

from afs_neighbourhood_analysis.pipeline import read_from_s3


def change_geographic_level(df, **kwargs):
    """
    Change the geographic level of a dataset converting between the following:
    - LSOA
    - MSOA
    - LAD
    - LEP
    - OA
    - Counties and Unitary Authorities
    """

    on = kwargs.get("on", "LSOA11CD")
    conv_from = kwargs.get("conv_from", "LSOA11CD")
    conv_to = kwargs.get("conv_to", "OA11CD")
    if conv_from in [
        "LSOA11CD",
        "MSOA11CD",
        "LAD21CD",
        "LEPOP21CD",
        "OA11CD",
    ] and conv_to in ["LSOA11CD", "MSOA11CD", "LAD21CD", "LEPOP21CD", "OA11CD"]:
        geo = read_from_s3.df_from_s3(
            "geography_conversions/Output_Area_to_Local_Authority_District_to_Lower_Layer_Super_Output_Area_to_Middle_Layer_Super_Output_Area_to_Local_Enterprise_Partnership_(April_2017)_Lookup_in_England_V2.csv"
        )
        conv_to_nm = conv_to.split("CD")[0] + "NM"
        if conv_to_nm == "OA11NM":
            geo = geo[[conv_from, conv_to]]
        else:
            geo = geo[[conv_from, conv_to, conv_to_nm]]
    elif conv_from in ["OA11CD", "CTYUA21CD"] and conv_to in ["OA11CD", "CTYUA21CD"]:
        geo = read_from_s3.df_from_s3(
            "geography_conversions/OA11_CTYUA21_EN_LU.xlsx",
            sheet_name="OA11_CTYUA21_EN_LU",
        )
        conv_to_nm = conv_to.split("CD")[0] + "NM"
        if conv_to_nm == "OA11NM":
            geo = geo[[conv_from, conv_to]]
        else:
            geo = geo[[conv_from, conv_to, conv_to_nm]]
    else:
        print(
            "Please pick both conv_from and conv_to from ONE of the following lists: ['LSOA11CD', 'MSOA11CD', 'LAD21CD', 'LEPOP21CD', 'OA11CD] OR ['OA11CD', 'CTYUA21CD']"
        )

    return df.merge(geo, on=on)


def process_ahah_columns(df):
    """
    Function to process the Access to Healthy Assets and Hazards columns into more readable format and convert geography if kwarg defined.
    """

    cols = read_from_s3.df_from_s3(
        "access_to_healthy_assets_and_hazards/data_sources.xlsx"
    )
    cols.dropna(inplace=True)

    column_mappings = {}
    column_mappings["lsoa11"] = "LSOA11CD"
    for idx, row in cols.iterrows():
        column_mappings[row["Name"]] = row["Description"]
        column_mappings[str(row["Name"]) + "_rnk"] = str(row["Description"]) + " Rank"
        column_mappings[str(row["Name"]) + "_pct"] = (
            str(row["Description"]) + " Percentiles"
        )

    df.rename(columns=column_mappings, inplace=True)

    df.columns = df.columns.str.strip().str.replace(r"[^a-zA-Z0-9_]", r"_", regex=True)

    return df
