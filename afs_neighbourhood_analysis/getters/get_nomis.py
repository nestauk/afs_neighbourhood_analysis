import logging
import pandas as pd
from datetime import date
import afs_neighbourhood_analysis

logger = logging.getLogger(__name__)
CELL_LIMIT = 25_000
REQUESTS_PER_SECOND = 2
project_dir = afs_neighbourhood_analysis.PROJECT_DIR

nomis_urls = {
    "aps_dependant_children_household_rate": "https://www.nomisweb.co.uk/api/v01/dataset/NM_137_1.data.csv?geography={geo}&households_children=1&eastatus=0&depchild=1&housetype=0&measures=20301",
    "aps_dependant_children_lone_parent_household_rate": "https://www.nomisweb.co.uk/api/v01/dataset/NM_137_1.data.csv?geography={geo}&households_children=1&eastatus=0&depchild=1&housetype=1&measures=20301",
    "aps_public_private_sector_employment": "https://www.nomisweb.co.uk/api/v01/dataset/NM_17_5.data.csv?geography={geo}&date={date}&variable=1463,1464&measures=20599,21001,21002,21003",
    "aps_unemployment_illness_more_than_year": "https://www.nomisweb.co.uk/api/v01/dataset/NM_17_5.data.csv?geography={geo}&date={date}&variable=1698&measures=20599,21001,21002,21003",
    "aps_economically_active_gcse_qualified": "https://www.nomisweb.co.uk/api/v01/dataset/NM_17_5.data.csv?geography={geo}&date={date}&variable=1153&measures=20599,21001,21002,21003",
    "aps_economically_inactive_take_care_of_family": "https://www.nomisweb.co.uk/api/v01/dataset/NM_17_5.data.csv?geography={geo}&date={date}&variable=1494&measures=20599,21001,21002,21003",
    "aps_unemployment_rate": "https://www.nomisweb.co.uk/api/v01/dataset/NM_17_5.data.csv?geography={geo}&date={date}&variable=83&measures=20599,21001,21002,21003",
    "aps_born_not_born_UK_by_ethnicity": "https://www.nomisweb.co.uk/api/v01/dataset/NM_17_5.data.csv?geography={geo}&date={date}&variable=861...864&measures=20599,21001,21002,21003",
    # EMPTY : "aps_workplace_employment_sub_occupations": "https://www.nomisweb.co.uk/api/v01/dataset/NM_100_1.data.csv?geography={geo}&date={date}&cell=405340417,405340673,405340929,405341185,405341441,405341697,405341953,405342209,405342465,405342721,405342977,405343233,405343489,405343745,405344001,405344257,405344513,405344769,405345025,405345281,405345537,405345793,405346049,405346305,405346561,405346817&measures=20100,20701",
    # EMPTY : "aps_workplace_employment_occupation_and_industry": "https://www.nomisweb.co.uk/api/v01/dataset/NM_100_1.data.csv?geography={geo}&date={date}&cell=403308801...403308810,403309057...403309066,403309313...403309322,403309569...403309578,403309825...403309834,403310081...403310090,403310337...403310346,403310593...403310602,403310849...403310858&measures=20100,20701",
    "ashe_earnings_resident_analysis": "https://www.nomisweb.co.uk/api/v01/dataset/NM_30_1.data.csv?geography={geo}&date={date}&sex=7&item=2&pay=7&measures=20100,20701",
    "bres_industry_percentage": "https://www.nomisweb.co.uk/api/v01/dataset/NM_189_1.data.csv?geography={geo}&industry=150994945...150994965&employment_status=1&measure=2&measures=20100",
    "claimant_count": "https://www.nomisweb.co.uk/api/v01/dataset/NM_162_1.data.csv?geography={geo}&date={date}&gender=0&age=0&measure=2&measures=20100",
    "jobseekers_allowance": "https://www.nomisweb.co.uk/api/v01/dataset/NM_102_1.data.csv?geography={geo}&date={date}&sex=7&item=1&occupation=524288...524297&age=0&duration=0&destination=0&measures=20100",
    "ra_household_income_per_head": "https://www.nomisweb.co.uk/api/v01/dataset/NM_185_1.data.csv?geography=1807745025...1807745028,1807745030...1807745032,1807745034...1807745083,1807745085,1807745282,1807745283,1807745086...1807745155,1807745157...1807745164,1807745166...1807745170,1807745172...1807745177,1807745179...1807745194,1807745196,1807745197,1807745199,1807745201...1807745218,1807745221,1807745222,1807745224,1807745226...1807745231,1807745233,1807745234,1807745236...1807745244,1807745271...1807745281&component_of_gdhi=0&measure=2&measures=20100",
}


def get_nomis():
    """
    Fetch NOMIS datasets using the URLS generated by the NOMIS API with variables
    """

    date_string = ""
    year_list = [i for i in range(2004, date.today().year)]
    years = []

    for year in year_list:
        years.append(f"{year}-12")
    date_string = date_string + ",".join(years)

    for dataset, url in nomis_urls.items():
        if dataset in [
            "bres_industry_percentage",
            "aps_dependant_children_household_rate",
        ]:
            url_updated = url.format(geo="TYPE463")
        elif dataset in ["household_income_per_head"]:
            url_updated = url
        else:
            url_updated = url.format(geo="TYPE463", date=date_string)

        # SAVE DATAFRAME
        print(f"Collecting dataset: {dataset}")
        pd.read_csv(url_updated).to_csv(
            f"{project_dir}/inputs/data/raw/nomis/nomis_{dataset}.csv"
        )


if __name__ == "__main__":
    get_nomis()
