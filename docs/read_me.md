# AFS Neighbourhood Analysis
(also known as Mapping LAs/Outperforming neighbourhoods)

## Key resources
* [This Google Sheet](https://docs.google.com/spreadsheets/d/1vkYA9tuoIa3P11RFRgrYL3bXneyDmbQ3zp0Xy7YQy-k/edit?usp=sharing) contains key links, datasets and reading which were investigated during the two week literature review sprint (w/c 07.02.2022).
* [This Miro board](https://miro.com/welcomeonboard/N1dHTTRqZ3dHbmdmMURORlo5eGxnQ09iTmZQem1wa3hsQ1pLSWVnaXd6Qk5DZ1U2UHhTOXdsNUFFV0VxbDVlcHwzMDc0NDU3MzQ4NTU5MTI3NDQ0?invite_link_id=940868712278) contains the conceptual model which summarises all the factors which affect school readiness and their datasets (incomplete).
* The paper which prompted Raj's idea is [Dobbie and Fryer, 2012](https://scholar.harvard.edu/files/fryer/files/dobbie_fryer_revision_final.pdf).
* There are a number of notes we made during the literature review, the most useful are listed below:
    * The Vulnerable Families Team at Swansea University's [Weighting of risk factors for low school readiness](https://docs.google.com/document/d/1oU957WpBeD08giz2xmAXSlSOxxosk6FNHggQR1QATAs/edit?usp=sharing)
    * Work from the University of Bristol - [On your marks: Measuring the school readiness of children in low-to-middle income families](https://docs.google.com/document/d/1KFTx9qBGdXS-1zyxtkK1cyNpQq1oQHeY-Verli5xvms/edit?usp=sharing)
    * And finally, [The role of early childhood education and care in shaping life chances: The changing face of early childhood in the UK](https://docs.google.com/document/d/1MaqWSCTooVLh07UeMVFtKQimSyiU0L7pi50tqrtJvuw/edit?usp=sharing)
* The Emerald scoping doc can be accessed [here](https://docs.google.com/document/d/1o6sb9jkG45uym6NL27xOELAZdnd7O_KUaaJzWLyMbAA/edit?usp=sharing).
    * This contains the [Gantt chart and timelines](https://docs.google.com/spreadsheets/d/16xM8FMAEZh0XkG1JSrh15D6KQptkuaneI9S6xtBYeow/edit?usp=sharing).

## Need to know parts of the GitHub repo
* `afs_neighbourhood_analysis/getters/get_education_data.py` contains the script to download the Education datasets off the DfE website.
    * The key file here is `APS_GLD_ELG_EXP_2013_2019.csv` which contains percentages reaching a Good Level of Development (GLD) for each Unitary Authority.
* The Fingertips PHE dataset is accessed via [their python package](https://fingertips-py.readthedocs.io/en/latest/)

## More detail on the outcome measure (GLD)
#### `APS_GLD_ELG_EXP_2013_2019.csv`
| time_period |	old_la_code |	new_la_code	| la_name |	gender | number_of_children | point_score | average_point_score	elg_number | elg_percent | gld_number | gld_percent | comm_lang_lit_number | comm_lang_lit_percent |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 201819 | 841 | E06000005 | Darlington | Total | 1198 | 40876 | 34.1 | 843 | 70.4 | 859 | 71.7 | 865 | 72.2
| 201819 | 841 | E06000005 | Darlington | Girls | 571 | 20336 | 	35.6 | 442 | 77.4 | 450 | 78.8 | 453 | 79.3
| 201819 | 841 | E06000005 | Darlington | Boys | 627 | 20540 | 32.8 | 401 | 64.0 | 409 | 65.2 | 412 | 65.7
| 201819 | 840 | E06000047 | Durham | Total	 | 5420 | 191188 | 35.3 | 3842 | 70.9 | 3890 | 71.8 | 3926 | 72.4
| 201819 | 840 | E06000047 | Durham | Girls | 2637 | 96722 | 36.7 | 2055 | 77.9 | 2065 | 78.3 | 2078 | 78.8

#### `AREAS_OF_LEARNING_2013_2019.csv`
| time_period |	old_la_code |	new_la_code |	la_name |	gender |	area_of_learning |	number_of_children |	at_least_expected_number |	exceeded_number	at_least_expected_percent |	exceeded_percent |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 201819 | 841 | E06000005 | Darlington | Total | All Prime Areas	 | 1198 |	920 | . | 76.8 | . | 
| 201819 | 841 | E06000005 | Darlington | Girls | All Prime Areas | 571 | 480 | . | 84.1 | . | 
| 201819 | 841 | E06000005 | Darlington | Boys | All Prime Areas | 627 | 440 | . | 70.2 | . | 
| 201819 | 840 | E06000047 | Durham | Total | All Prime Areas | 5420 | 4284 | . | 79.0 | . | 
| 201819 | 840 | E06000047 | Durham | Girls | All Prime Areas | 2637 | 2260 | . | 85.7 | . | 
#### `ELG_2013_2019.csv`
| time_period | old_la_code | new_la_code | la_name | gender | elg_category | number_of_children | emerging_number | expected_number | exceeded_number | at_least_expected_number | emerging_percent | expected_percent | exceeded_percent | at_least_expected_percent |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 201819 | 841 | E06000005 | Darlington | Total | Listening and attention | 1198 | 229 | 673 | 296 | 969 | 19.1 | 56.2 | 24.7 | 80.9 |
| 201819 | 841 | E06000005 | Darlington | Girls | Listening and attention | 571 | 72 | 324 | 175 | 499 | 12.6 | 56.7 | 30.6 | 87.4 |
| 201819 | 841 | E06000005 | Darlington | Boys | Listening and attention | 627 | 157 | 349 | 121 | 470 | 25.0 | 55.7 | 19.3 | 75.0 |
| 201819 | 840 | E06000047 | Durham | Total | Listening and attention | 5420 | 807 | 3152 | 1461 | 4613 | 14.9 | 58.2 | 27.0 | 85.1 |
| 201819 | 840 | E06000047 | Durham | Girls | Listening and attention | 2637 | 243 | 1524 | 870 | 2394 | 9.2 | 57.8 | 33.0 | 90.8 | 
#### `EYFSP_LA_1_key_measures_additional_tables_2013_2019.xlsx`

| time_period | old_la_code | new_la_code | la_name | gender | characteristic | characteristic_type | number_of_pupils | elg_number | elg_percent | gld_number | gld_percent | point_score | average_point_score |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 201819 | 841 | E06000005 | Darlington | Total | Ethnicity | Total | 1198 | 843 | 70 | 859 | 72 | 40876 | 34.1 |
| 201819 | 841 | E06000005 | Darlington | Total | Ethnicity | White | 1064 | 756 | 71 | 769 | 72 | 36459 | 34.3 |
| 201819 | 841 | E06000005 | Darlington | Total | Ethnicity | Asian | 52 | 33 | 63 | 35 | 67 | 1669 | 32.1 |
| 201819 | 841 | E06000005 | Darlington | Total | Ethnicity | Black | 9 | 8 | 89 | 8 | 89 | 342 | 38 |
| 201819 | 841 | E06000005 | Darlington | Total | Ethnicity | Chinese | 2 | 2 | 100 | 2	100 | 79 | 39.5 |

#### `EYFSP_LA_2_com_lit_maths_additional_tables_2013_2019.xlsx`
| time_period | old_la_code | new_la_code | la_name | fsm | area_of_learning | number_of_pupils | at_least_expected_number | at_least_expected_percent |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 201819 | 841 | E06000005 | Darlington | Total | Communication and Language | 1198 | 936 | 78 |
| 201819 | 841 | E06000005 | Darlington | FSM | Communication and Language | 238 | 159 | 67 |
| 201819 | 841 | E06000005 | Darlington | All other pupils | Communication and Language | 960 | 777 | 81 |
| 201819 | 840 | E06000047 | Durham | Total | Communication and Language | 5420 | 4422 | 82 |
| 201819 | 840 | E06000047 | Durham | FSM | Communication and Language | 1282 | 877 | 68 |
