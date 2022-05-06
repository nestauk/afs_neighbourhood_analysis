from afs_neighbourhood_analysis import PROJECT_DIR
from afs_neighbourhood_analysis.pipeline.get_education_data import get_data


def main():

    # get EYFSP specific data nb: SFR = Statistical First Release

    member_files_eyfsp = [
        "APS_GLD_ELG_EXP_2013_2019.csv",
        "AREAS_OF_LEARNING_2013_2019.csv",
        "ELG_2013_2019.csv",
        "EYFSP_LA_1_key_measures_additional_tables_2013_2019.xlsx",
        "EYFSP_LA_2_com_lit_maths_additional_tables_2013_2019.xlsx",
        "EYFSP_LAD_1_key_measures_additional_tables_2019.xlsx",
        "EYFSP_LAD_1_key_measures_additional_tables_2018.csv",
        "EYFSP_LAD_2_ELG_additional_tables_2019.xlsx",
        "EYFSP_LAD_2_ELG_additional_tables_2018.csv",
        "EYFSP_LAD_pr_additional_tables_2014_2019.xlsx",
        "SFR60_2015_2016_2017_UD_LA2_additional table (002).csv",
        "SFR60_2017_GIRLS_UD.csv",
        "SFR60_2017_BOYS_UD.csv",
        "SFR60_2017_UD_LA_additional tables.csv",
        "SFR60_2017_UD_LA_additional tables.csv",
        "SFR60_2017_UD_LAD.csv",
        "SFR50_2016_UD_LA_additional tables.csv",
        "SFR50_2016_GIRLS_UD.csv",
        "SFR50_2016_BOYS_UD.csv",
        "SFR50_2016_ALL_UD.csv",
        "SFR47_2013_UD_LA.csv",
        "SFR46_2014_UD_LA.csv",
        "SFR43_2013_IMD_UD.csv",
        "SFR43_2013_Girls_UD.csv",
        "SFR43_2013_Boys_UD.csv",
        "SFR43_2013_All_UD.csv",
        "SFR39_2014_IMD_UD.csv",
        "SFR39_2014_GIRLS_UD.csv",
        "SFR39_2014_BOYS_UD.csv",
        "SFR39_2014_ALL_UD.csv",
        "SFR36_2015_UD_LA_additional tables.csv",
        "SFR36_2015_Girls_UD.csv",
        "SFR36_2015_Boys_UD.csv",
        "SFR36_2015_All_UD_csv.csv",
        "SFR30_2012_UD_LA.csv",
        "SFR29_2011_UD_LA.csv",
        "SFR28_2010_IMD_UD.csv",
        "SFR28_2010_Girls_UD.csv",
        "SFR28_2010_Boys_UD.csv",
        "SFR28_11_IMD_UD.csv",
        "SFR28_11_Girls_UD.csv",
        "SFR28_11_Boys_UD.csv",
        "SFR23_2012_IMD_UD.csv",
        "SFR23_2012_GIRLS_UD.csv",
        "SFR23_2012_BOYS_UD.csv",
    ]

    get_data(
        url="https://www.gov.uk/government/collections/statistics-early-years-foundation-stage-profile",
        folder_name="eyfsp",
        member_files=member_files_eyfsp,
    )

    # get provision data

    get_data(
        url="https://explore-education-statistics.service.gov.uk/find-statistics/education-provision-children-under-5",
        folder_name="provision",
    )

    return
