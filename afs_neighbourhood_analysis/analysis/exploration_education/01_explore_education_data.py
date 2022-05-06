# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     comment_magics: true
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.7
#   kernelspec:
#     display_name: afs_neighbourhood_analysis
#     language: python
#     name: afs_neighbourhood_analysis
# ---

# %% [markdown]
# # EDA of Education datasets

# %% [markdown]
# ## 1. Notebook setup

# %%
# %load_ext autoreload

# %%
# %autoreload 2

# %%
import pandas as pd
import numpy as np
import altair as alt
import geopandas as gpd

# %%
from afs_neighbourhood_analysis.utils import utils
from afs_neighbourhood_analysis.pipeline.get_education_data import get_data
from afs_neighbourhood_analysis.pipeline.generate_data import main
from afs_neighbourhood_analysis import PROJECT_DIR

# %%
from afs_neighbourhood_analysis.pipeline.TMP_eyfsp_getter import get_edu_dataframes

# %%
tmp = get_edu_dataframes()

# %%
# main()

# %%
colours = utils.load_colours()
for key, val in colours.items():
    if key == "nesta_colours_new":
        nesta_colours = val

# %%
alt.themes.register("nestafont", utils.nestafont)
alt.themes.enable("nestafont")

# %%
input_fpath = f"{PROJECT_DIR}/inputs/data/aux"

# %%
output_fpath = f"{PROJECT_DIR}/outputs"

# %% [markdown]
# ## 2. Read in data

# %% [markdown]
# ### 2.1 Read in EYFSP data

# %% [markdown]
# #### 2.1.1 2013-2019 single datasets

# %%
aps_gld_elg_expr_2013_2019 = pd.read_csv(
    f"{input_fpath}/eyfsp/APS_GLD_ELG_EXP_2013_2019.csv"
)

# %%
areas_of_learning_2013_2019 = pd.read_csv(
    f"{input_fpath}/eyfsp/AREAS_OF_LEARNING_2013_2019.csv"
)

# %%
elg_2013_2019 = pd.read_csv(f"{input_fpath}/eyfsp/ELG_2013_2019.csv")

# %%
eyfsp_la_1_key_measures_additional_tables_2013_2019 = pd.read_excel(
    f"{input_fpath}/eyfsp/EYFSP_LA_1_key_measures_additional_tables_2013_2019.xlsx",
    engine="openpyxl",
)

# %%
eyfsp_la_2_com_lit_maths_additional_tables_2013_2019 = pd.read_excel(
    f"{input_fpath}/eyfsp/EYFSP_LA_2_com_lit_maths_additional_tables_2013_2019.xlsx",
    engine="openpyxl",
)

# %%
test = pd.read_excel(
    f"{input_fpath}/eyfsp/EYFSP_LAD_pr_additional_tables_2014_2019.xlsx",
    engine="openpyxl",
)

# %%
areas_of_learning_2013_2019.replace(".", np.nan, inplace=True)

# %% [markdown]
# #### 2.1.2 2019 LAD 2 ELG additional tables

# %%
fsm_2019 = pd.read_excel(
    f"{input_fpath}/eyfsp/EYFSP_LAD_2_ELG_additional_tables_2019.xlsx",
    engine="openpyxl",
)

# %%
fsm_2018 = pd.read_csv(
    f"{input_fpath}/eyfsp/EYFSP_LAD_2_ELG_additional_tables_2018.csv"
)

# %%
ethnicity_fsm_gender_school_readiness = pd.read_csv(
    f"{input_fpath}/eyfsp/by-ethnicity-gender-and-eligibility-for-free-school-meals-table.csv",
    header=0,
)

# %% [markdown]
# ### 2.2 Read in Geodata

# %%
county_unitary_authority_boundaries = gpd.read_file(
    f"{input_fpath}/geodata/Counties_and_Unitary_Authorities_(December_2019)_Boundaries_UK_BUC/Counties_and_Unitary_Authorities_(December_2019)_Boundaries_UK_BUC.shp"
).to_crs(epsg=4326)

# %%
county_unitary_authority_boundaries.columns

# %%
london_boroughs = pd.read_csv(f"{input_fpath}/geodata/london_boroughs.csv")

# %%
IMD = gpd.read_file(f"{input_fpath}/geodata/IMD_2019/IMD_2019.shp").to_crs(epsg=4326)

# %%
conversion_LAS_county = pd.read_csv(
    f"{input_fpath}/Local_Authority_District_to_County_(April_2021)_Lookup_in_England.csv"
)

# %%
IMD_grouped = IMD.groupby("LADcd").mean().reset_index()

# %%
IMD_county = IMD_grouped.merge(
    conversion_LAS_county, left_on="LADcd", right_on="LAD21CD", how="left"
)

# %%
IMD_gld = IMD_grouped.merge(
    aps_gld_elg_expr_2013_2019[
        (aps_gld_elg_expr_2013_2019.time_period == 201819)
        & (aps_gld_elg_expr_2013_2019.gender == "Total")
    ],
    left_on="LADcd",
    right_on="new_la_code",
    how="left",
)

# %%
IMD_gld_grouped = IMD_gld.groupby("la_name").mean().reset_index()

# %%
IMD_county_grouped = IMD_county.groupby("CTY21NM").mean().reset_index()

# %%
IMD_gld_county = IMD_county_grouped.merge(
    aps_gld_elg_expr_2013_2019[
        (aps_gld_elg_expr_2013_2019.time_period == 201819)
        & (aps_gld_elg_expr_2013_2019.gender == "Total")
    ],
    left_on="CTY21NM",
    right_on="la_name",
    how="left",
)

# %%
IMD_gld_county_grouped = IMD_gld_county.groupby("CTY21NM").mean().reset_index()

# %%
IMD_combined = pd.concat([IMD_gld_grouped, IMD_gld_county_grouped])

# %%
IMD_combined.dropna(subset="time_period", inplace=True)

# %%
IMD_combined["la_name"].update(IMD_combined.pop("CTY21NM"))

# %% [markdown]
# ## 3. Cleaning

# %%
aps_gld_elg_expr_2013_2019 = aps_gld_elg_expr_2013_2019[
    aps_gld_elg_expr_2013_2019.geographic_level == "Local Authority"
]

# %%
aps_gld_elg_expr_2013_2019.drop(
    columns=[
        "time_identifier",
        "geographic_level",
        "country_code",
        "country_name",
        "region_code",
        "region_name",
    ],
    inplace=True,
)

# %%
areas_of_learning_2013_2019 = areas_of_learning_2013_2019[
    areas_of_learning_2013_2019.geographic_level == "Local Authority"
]

# %%
areas_of_learning_2013_2019.drop(
    columns=[
        "time_identifier",
        "geographic_level",
        "country_code",
        "country_name",
        "region_code",
        "region_name",
    ],
    inplace=True,
)

# %%
elg_2013_2019 = elg_2013_2019[elg_2013_2019.geographic_level == "Local Authority"]

# %%
elg_2013_2019.drop(
    columns=[
        "time_identifier",
        "geographic_level",
        "country_code",
        "country_name",
        "region_code",
        "region_name",
    ],
    inplace=True,
)

# %%
eyfsp_la_1_key_measures_additional_tables_2013_2019 = (
    eyfsp_la_1_key_measures_additional_tables_2013_2019[
        eyfsp_la_1_key_measures_additional_tables_2013_2019.geographic_level
        == "Local Authority"
    ]
)

# %%
eyfsp_la_1_key_measures_additional_tables_2013_2019

# %%
eyfsp_la_1_key_measures_additional_tables_2013_2019.drop(
    columns=[
        "time_identifier",
        "geographic_level",
        "country_code",
        "country_name",
        "region_code",
        "region_name",
    ],
    inplace=True,
)

# %% [markdown]
# ## 4. Descriptive stats

# %%
gld_data_to_plot = aps_gld_elg_expr_2013_2019[
    (aps_gld_elg_expr_2013_2019.gender == "Total")
    & (aps_gld_elg_expr_2013_2019.time_period == 201819)
]

# %%
gld_girls = aps_gld_elg_expr_2013_2019[
    (aps_gld_elg_expr_2013_2019.gender == "Girls")
    & (aps_gld_elg_expr_2013_2019.time_period == 201819)
]

# %%
gld_boys = aps_gld_elg_expr_2013_2019[
    (aps_gld_elg_expr_2013_2019.gender == "Boys")
    & (aps_gld_elg_expr_2013_2019.time_period == 201819)
]

# %%
gld_left = gld_girls[["gld_percent", "new_la_code"]].rename(
    columns={"gld_percent": "gld_percent_girls"}
)
gld_right = gld_boys.rename(columns={"gld_percent": "gld_percent_boys"})

# %%
gld_both = gld_left.merge(gld_right, on="new_la_code", how="right")

# %%
gld_both["gld_diff"] = gld_both["gld_percent_girls"] - gld_both["gld_percent_boys"]

# %%
aps_gld_elg_expr_2013_2019.sort_values(by=["time_period", "la_name"], inplace=True)
aps_gld_elg_expr_2013_2019.reset_index(inplace=True)

# %%
aps_gld_elg_expr_2013_2019["pct_pt_change_gld_girls"] = (
    aps_gld_elg_expr_2013_2019[(aps_gld_elg_expr_2013_2019.gender == "Girls")].groupby(
        "new_la_code"
    )["gld_percent"]
).diff(1)

# %%
aps_gld_elg_expr_2013_2019["pct_pt_change_gld_boys"] = (
    aps_gld_elg_expr_2013_2019[(aps_gld_elg_expr_2013_2019.gender == "Boys")].groupby(
        "new_la_code"
    )["gld_percent"]
).diff(1)

# %%
aps_gld_elg_expr_2013_2019["pct_pt_change_gld_girls"].update(
    aps_gld_elg_expr_2013_2019.pop("pct_pt_change_gld_boys")
)

# %%
aps_gld_elg_expr_2013_2019.rename(
    columns={"pct_pt_change_gld_girls": "pct_pt_change_gld"}, inplace=True
)

# %%
aps_gld_elg_expr_2013_2019.drop(columns="index", inplace=True)

# %%
chart_IMD = (
    alt.Chart(IMD_combined)
    .mark_circle(size=30, color="#0000FF")
    .encode(
        x=alt.X(
            "IMD_Decile",
            title="Mean IMD Decile based on LAs",
            scale=alt.Scale(domain=[1, 10]),
        ),
        y=alt.Y(
            "gld_percent", title="Mean GLD percentage", scale=alt.Scale(domain=[50, 90])
        ),
        tooltip=["la_name", "gld_percent", "IMD_Decile"],
    )
    .properties(title="IMD Decile  (1 - most deprived, 10 - least deprived)")
)

gld_total = (
    alt.Chart(gld_data_to_plot)
    .mark_bar(color="#0000FF")
    .encode(
        alt.X("gld_percent:Q", bin=True, title="GLD Percentage"),
        y=alt.Y("count()", title="Count"),
    )
    .properties(title="GLD Total")
)

gld_boys_v_girls = (
    alt.Chart(
        aps_gld_elg_expr_2013_2019[
            (aps_gld_elg_expr_2013_2019.time_period == 201819)
            & (aps_gld_elg_expr_2013_2019.gender != "Total")
        ]
    )
    .mark_bar()
    .encode(
        alt.X("gld_percent:Q", bin=True, title="GLD Percentage"),
        y=alt.Y("count()", title="Count"),
        color=alt.Color(
            "gender",
            scale=alt.Scale(domain=["Boys", "Girls"], range=["#FDB633", "#18A48C"]),
        ),
    )
    .properties(title="GLD for boys v girls")
)

gld_trends = (
    alt.Chart(
        aps_gld_elg_expr_2013_2019[(aps_gld_elg_expr_2013_2019.gender != "Total")]
    )
    .mark_line()
    .encode(
        x=alt.X("time_period:N", title="Time period"),
        y=alt.Y(
            "mean(gld_percent):Q",
            stack=None,
            title="Mean of GLD percentage",
            scale=alt.Scale(domain=[30, 90]),
        ),
        color=alt.Color(
            "gender",
            scale=alt.Scale(domain=["Boys", "Girls"], range=["#FDB633", "#18A48C"]),
        ),
    )
    .properties(title="Trends in boys v girls over time")
)

gld_percentage_trends = (
    alt.Chart(
        aps_gld_elg_expr_2013_2019[(aps_gld_elg_expr_2013_2019.gender != "Total")]
    )
    .mark_line()
    .encode(
        x=alt.X("time_period:N", title="Time period"),
        y=alt.Y(
            "mean(pct_pt_change_gld):Q",
            stack=None,
            title="Mean change in percentage points each year",
        ),
        color=alt.Color(
            "gender",
            scale=alt.Scale(domain=["Boys", "Girls"], range=["#FDB633", "#18A48C"]),
        ),
    )
    .properties(title="Mean percentage point change in GLD for each year")
)

# %%
dataframe_to_iterate_over = aps_gld_elg_expr_2013_2019[
    aps_gld_elg_expr_2013_2019.number_of_children >= 100
]

# %%
LAs = []
pct_changes = []
genders = []

for la_name_ in dataframe_to_iterate_over.la_name.unique():
    subset_df = dataframe_to_iterate_over[dataframe_to_iterate_over.la_name == la_name_]
    for gender_ in subset_df.gender.unique():
        subset_df_gender = subset_df[subset_df.gender == gender_]
        subset_df_gender = subset_df_gender.reset_index()
        try:
            pct_changes.append(
                subset_df_gender.gld_percent.iloc[-1]
                - subset_df_gender.gld_percent.iloc[1]
            )
            LAs.append(la_name_)
            genders.append(gender_)
        except:
            print(la_name_)

# %%
pct_change_per_LA_per_gender = pd.DataFrame(
    {"la_name": LAs, "gender": genders, "pct_pt_change": pct_changes}
)

# %%
worst_pct_change_boys = (
    pct_change_per_LA_per_gender[pct_change_per_LA_per_gender.gender == "Boys"]
    .sort_values(by="pct_pt_change")[:10]
    .copy()
)
worst_pct_change_girls = (
    pct_change_per_LA_per_gender[pct_change_per_LA_per_gender.gender == "Girls"]
    .sort_values(by="pct_pt_change")[:10]
    .copy()
)

# %%
best_pct_change_boys = (
    pct_change_per_LA_per_gender[pct_change_per_LA_per_gender.gender == "Boys"]
    .sort_values(by="pct_pt_change", ascending=False)[:10]
    .copy()
)
best_pct_change_girls = (
    pct_change_per_LA_per_gender[pct_change_per_LA_per_gender.gender == "Girls"]
    .sort_values(by="pct_pt_change", ascending=False)[:10]
    .copy()
)

# %%
dataset_1 = aps_gld_elg_expr_2013_2019[
    (aps_gld_elg_expr_2013_2019.gender == "Boys")
    & (aps_gld_elg_expr_2013_2019.la_name.isin(list(worst_pct_change_boys.la_name)))
]
dataset_2 = aps_gld_elg_expr_2013_2019[
    (aps_gld_elg_expr_2013_2019.gender == "Girls")
    & (aps_gld_elg_expr_2013_2019.la_name.isin(list(worst_pct_change_girls.la_name)))
]

dataset_3 = aps_gld_elg_expr_2013_2019[
    (aps_gld_elg_expr_2013_2019.gender == "Boys")
    & (aps_gld_elg_expr_2013_2019.la_name.isin(list(best_pct_change_boys.la_name)))
]
dataset_4 = aps_gld_elg_expr_2013_2019[
    (aps_gld_elg_expr_2013_2019.gender == "Girls")
    & (aps_gld_elg_expr_2013_2019.la_name.isin(list(best_pct_change_girls.la_name)))
]


# %%
def plot_interactive_line_graph(dataset, title=""):
    highlight = alt.selection(
        type="single", on="mouseover", fields=["la_name"], nearest=True
    )

    base = alt.Chart(dataset).encode(
        x=alt.X("time_period:N", title="Time period"),
        y=alt.Y(
            "mean(pct_pt_change_gld):Q",
            stack=None,
            title="Mean change in percentage each year",
        ),
        color=alt.Color(
            "la_name",
            scale=alt.Scale(
                domain=list(dataset.la_name),
                range=[
                    nesta_colours[0],
                    nesta_colours[1],
                    nesta_colours[2],
                    nesta_colours[3],
                    nesta_colours[4],
                    nesta_colours[5],
                    nesta_colours[10],
                    nesta_colours[7],
                    nesta_colours[8],
                    nesta_colours[9],
                ],
            ),
        ),
        tooltip=["la_name"],
    )

    points = (
        base.mark_circle()
        .encode(opacity=alt.value(0))
        .add_selection(highlight)
        .properties(width=1000, height=500)
    )

    lines = base.mark_line().encode(
        size=alt.condition(~highlight, alt.value(1), alt.value(3))
    )

    return (points + lines).properties(title=title)


# %%
charts_worst = alt.hconcat(
    plot_interactive_line_graph(
        dataset_1, title="Smallest percentage change in GLD 2012-2019 (boys)"
    ),
    plot_interactive_line_graph(
        dataset_2, title="Smallest percentage change in GLD 2012-2019 (girls)"
    ),
).resolve_scale(color="independent")
charts_best = alt.hconcat(
    plot_interactive_line_graph(
        dataset_3, title="Largest percentage change in GLD 2012-2019 (boys)"
    ),
    plot_interactive_line_graph(
        dataset_4, title="Largest percentage change in GLD 2012-2019 (girls)"
    ),
).resolve_scale(color="independent")

# %%
alt.vconcat(charts_worst, charts_best)

# %%
charts_2018_2019 = alt.hconcat(chart_IMD, gld_total, gld_boys_v_girls).properties(
    title="2018 - 2019 dataset"
)

# %%
charts_gld_trends = alt.hconcat(gld_trends, gld_percentage_trends)

# %%
alt.vconcat(charts_2018_2019, charts_gld_trends)

# %% [markdown]
# eyfsp_la_1_key_measures_additional_tables_2013_2019## 5. Maps

# %%
source = eyfsp_la_1_key_measures_additional_tables_2013_2019

# %%
source_filtered = source[
    (source.characteristic == "FSM eligibility")
    & (source.characteristic_type == "FSM")
    & (source.gender == "Total")
    & (source.time_period == 201819)
    & (source.gld_percent != ".")
]

# %%
gld_data_to_plot = county_unitary_authority_boundaries.merge(
    gld_data_to_plot, left_on="ctyua19cd", right_on="new_la_code", how="right"
)

# %%
fsm_data_to_plot = county_unitary_authority_boundaries.merge(
    source_filtered, left_on="ctyua19cd", right_on="new_la_code", how="right"
)

# %%
gld_diff_to_plot = county_unitary_authority_boundaries.merge(
    gld_both, left_on="ctyua19cd", right_on="new_la_code", how="right"
)

# %%
gld_data_to_plot["gld_rank"] = gld_data_to_plot["gld_percent"].rank(ascending=False)

# %%
bins = [60, 65, 70, 75, 80, 85, 90]
labels = ["60-65", "65-70", "70-75", "75-80", "80-85", "85-90"]

# %%
bins_fsm = [40, 45, 50, 55, 60, 65, 70, 75]
labels_fsm = ["40-45", "45-50", "50-55", "55-60", "60-65", "65-70", "70-75"]

# %%
gld_data_to_plot["binned_gld_percent"] = pd.cut(
    gld_data_to_plot.gld_percent, bins, labels=labels
)

# %%
fsm_data_to_plot["binned_gld_percent"] = pd.cut(
    fsm_data_to_plot.gld_percent, bins_fsm, labels=labels_fsm
)

# %%
bins_diff = [-15, -10, -5, 0, 5, 10, 15, 20]
labels_diff = ["-15 - -10", "-10 - -5", "-5 - 0", "0-5", "5-10", "10-15", "15-20"]

# %%
gld_diff_to_plot["binned_gld_diff"] = pd.cut(
    gld_diff_to_plot.gld_diff, bins_diff, labels=labels_diff
)

# %%
gld_data_to_plot = gpd.GeoDataFrame(gld_data_to_plot, geometry="geometry")
gld_diff_to_plot = gpd.GeoDataFrame(gld_diff_to_plot, geometry="geometry")

# %%
domain = labels
range_ = ["#2A2B2A", "#5E4955", "#996888", "#C99DA3", "#C6DDF0", "#759FBC"]

# %%
domain_fsm = labels_fsm
range_fsm = [
    "#f0f9e8",
    "#ccebc5",
    "#a8ddb5",
    "#7bccc4",
    "#4eb3d3",
    "#2b8cbe",
    "#08589e",
]

# %%
la_select = alt.selection_multi(fields=["la_name"])
color = alt.condition(
    la_select,
    alt.Color("binned_gld_percent:N", scale=alt.Scale(domain=domain, range=range_)),
    alt.value("lightgray"),
)

# %%
la_select_fsm = alt.selection_multi(fields=["la_name"])
color = alt.condition(
    la_select_fsm,
    alt.Color(
        "binned_gld_percent:N", scale=alt.Scale(domain=domain_fsm, range=range_fsm)
    ),
    alt.value("lightgray"),
)

# %%
la_select_diff = alt.selection_multi(fields=["la_name"])
color_diff = alt.condition(
    la_select,
    alt.Color("binned_gld_diff:N", scale=alt.Scale(scheme="redblue")),
    alt.value("lightgray"),
)

# %%
choro_gld_no_london_fsm = (
    alt.Chart(
        fsm_data_to_plot[
            ~fsm_data_to_plot.new_la_code.isin(list(london_boroughs.lad19cd))
        ]
    )
    .mark_geoshape(stroke="black")
    .encode(
        color=color,
        tooltip=[
            alt.Tooltip("la_name:N", title="LA"),
            alt.Tooltip("gld_percent:Q", title="Average GLD (%)", format="1.2f"),
            alt.Tooltip(
                "number_of_pupils:Q", title="Number of pupils (FSM)", format="1.2f"
            ),
        ],
    )
    .add_selection(la_select_fsm)
    .properties(width=500, height=600)
)

# %%
choro_gld_no_london = (
    alt.Chart(
        gld_data_to_plot[
            ~gld_data_to_plot.new_la_code.isin(list(london_boroughs.lad19cd))
        ]
    )
    .mark_geoshape(stroke="black")
    .encode(
        color=color,
        tooltip=[
            alt.Tooltip("la_name:N", title="LA"),
            alt.Tooltip("gld_percent:Q", title="Average GLD (%)", format="1.2f"),
        ],
    )
    .add_selection(la_select)
    .properties(width=500, height=600)
)

# %%
choro_gld_no_london_diff = (
    alt.Chart(
        gld_diff_to_plot[
            ~gld_diff_to_plot.new_la_code.isin(list(london_boroughs.lad19cd))
        ]
    )
    .mark_geoshape(stroke="black")
    .encode(
        color=color_diff,
        tooltip=[
            alt.Tooltip("la_name:N", title="LA"),
            alt.Tooltip(
                "gld_diff:Q",
                title="Difference between girls and boys (%)",
                format="1.2f",
            ),
        ],
    )
    .add_selection(la_select_diff)
    .properties(width=500, height=600)
)

# %%
choro_gld_london = (
    alt.Chart(
        gld_data_to_plot[
            gld_data_to_plot.new_la_code.isin(list(london_boroughs.lad19cd))
        ]
    )
    .mark_geoshape(stroke="black")
    .encode(
        color=color,
        tooltip=[
            alt.Tooltip("la_name:N", title="LA"),
            alt.Tooltip("gld_percent:Q", title="Average GLD (%)", format="1.2f"),
        ],
    )
    .add_selection(la_select)
    .properties(width=300, height=250)
)

# %%
choro_gld_london_fsm = (
    alt.Chart(
        fsm_data_to_plot[
            fsm_data_to_plot.new_la_code.isin(list(london_boroughs.lad19cd))
        ]
    )
    .mark_geoshape(stroke="black")
    .encode(
        color=color,
        tooltip=[
            alt.Tooltip("la_name:N", title="LA"),
            alt.Tooltip("gld_percent:Q", title="Average GLD (%)", format="1.2f"),
            alt.Tooltip(
                "number_of_pupils:Q", title="Number of pupils (FSM)", format="1.2f"
            ),
        ],
    )
    .add_selection(la_select_fsm)
    .properties(width=300, height=250)
)

# %%
choro_gld_london_diff = (
    alt.Chart(
        gld_diff_to_plot[
            gld_diff_to_plot.new_la_code.isin(list(london_boroughs.lad19cd))
        ]
    )
    .mark_geoshape(stroke="black")
    .encode(
        color=color_diff,
        tooltip=[
            alt.Tooltip("la_name:N", title="LA"),
            alt.Tooltip(
                "gld_diff:Q",
                title="Difference between girls and boys (%)",
                format="1.2f",
            ),
        ],
    )
    .add_selection(la_select)
    .properties(width=300, height=250)
)

# %%
bar_chart_highest = (
    (alt.Chart(gld_data_to_plot.sort_values(by="gld_percent", ascending=False)[:20]))
    .mark_bar(color="#18A48C")
    .encode(
        y=alt.Y(
            "la_name",
            sort=alt.EncodingSortField("gld_percent", op="sum", order="descending"),
            title="LAD Region",
        ),
        x=alt.X(
            f"gld_percent",
            title="LAD with the highest percentage of school ready children",
        ),
    )
    .add_selection(la_select)
    .properties(height=250, width=300)
)

# %%
bar_chart_highest_fsm = (
    (alt.Chart(fsm_data_to_plot.sort_values(by="gld_percent", ascending=False)[:20]))
    .mark_bar(color="#18A48C")
    .encode(
        y=alt.Y(
            "la_name",
            sort=alt.EncodingSortField("gld_percent", op="sum", order="descending"),
            title="LAD Region",
        ),
        x=alt.X(
            f"gld_percent",
            title="LAD with the highest percentage of school ready children",
        ),
    )
    .add_selection(la_select_fsm)
    .properties(height=250, width=300)
)

# %%
bar_chart_highest_diff = (
    (alt.Chart(gld_diff_to_plot.sort_values(by="gld_diff", ascending=False)[:20]))
    .mark_bar(color="#18A48C")
    .encode(
        y=alt.Y(
            "la_name",
            sort=alt.EncodingSortField("gld_diff", op="sum", order="descending"),
            title="LAD Region",
        ),
        x=alt.X(
            f"gld_diff",
            title="LAD with the highest percentage difference between girls and boys (girls do better than boys)",
        ),
    )
    .add_selection(la_select_diff)
    .properties(height=250, width=300)
)

# %%
bar_chart_lowest = (
    (
        alt.Chart(gld_data_to_plot.sort_values(by="gld_percent", ascending=True)[:20])
        .mark_bar(color="#FF6E47")
        .encode(
            y=alt.Y(
                "la_name",
                sort=alt.EncodingSortField("gld_percent", op="sum", order="descending"),
                title="LAD Region",
            ),
            x=alt.X(
                f"gld_percent",
                title="LAD with the lowest percentage of school ready children",
            ),
        )
    )
    .add_selection(la_select)
    .properties(height=250, width=300)
)

# %%
bar_chart_lowest_fsm = (
    (
        alt.Chart(fsm_data_to_plot.sort_values(by="gld_percent", ascending=True)[:20])
        .mark_bar(color="#FF6E47")
        .encode(
            y=alt.Y(
                "la_name",
                sort=alt.EncodingSortField("gld_percent", op="sum", order="descending"),
                title="LAD Region",
            ),
            x=alt.X(
                f"gld_percent",
                title="LAD with the lowest percentage of school ready children",
            ),
        )
    )
    .add_selection(la_select_fsm)
    .properties(height=250, width=300)
)

# %%
bar_chart_lowest_diff = (
    (
        alt.Chart(gld_diff_to_plot.sort_values(by="gld_diff", ascending=True)[:20])
        .mark_bar(color="#FF6E47")
        .encode(
            y=alt.Y(
                "la_name",
                sort=alt.EncodingSortField("gld_diff", op="sum", order="descending"),
                title="LAD Region",
            ),
            x=alt.X(
                f"gld_diff",
                title="LAD with the lowest percentage difference between girls and boys (and when boys do better than girls)",
            ),
        )
    )
    .add_selection(la_select_diff)
    .properties(height=250, width=300)
)

# %%
map_and_bar_ldn = alt.vconcat(bar_chart_highest, choro_gld_london).resolve_scale(
    color="independent"
)
alt.hconcat(choro_gld_no_london, map_and_bar_ldn).configure_view(
    strokeWidth=0
).resolve_scale(color="independent")

# %%
map_and_bar_ldn = alt.vconcat(bar_chart_lowest, choro_gld_london).resolve_scale(
    color="independent"
)
alt.hconcat(choro_gld_no_london, map_and_bar_ldn).configure_view(
    strokeWidth=0
).resolve_scale(color="independent")

# %%
map_and_bar_ldn_fsm = alt.vconcat(
    bar_chart_highest_fsm, choro_gld_london_fsm
).resolve_scale(color="independent")
alt.hconcat(choro_gld_no_london_fsm, map_and_bar_ldn_fsm).configure_view(
    strokeWidth=0
).resolve_scale(color="independent")

# %%
map_and_bar_ldn_fsm = alt.vconcat(
    bar_chart_lowest_fsm, choro_gld_london_fsm
).resolve_scale(color="independent")
alt.hconcat(choro_gld_no_london_fsm, map_and_bar_ldn_fsm).configure_view(
    strokeWidth=0
).resolve_scale(color="independent")

# %%
map_and_bar_ldn_diff = alt.vconcat(
    bar_chart_highest_diff, choro_gld_london_diff
).resolve_scale(color="independent")
alt.hconcat(choro_gld_no_london_diff, map_and_bar_ldn_diff).configure_view(
    strokeWidth=0
).resolve_scale(color="independent")

# %%
map_and_bar_ldn_diff = alt.vconcat(
    bar_chart_lowest_diff, choro_gld_london_diff
).resolve_scale(color="independent")
alt.hconcat(choro_gld_no_london_diff, map_and_bar_ldn_diff).configure_view(
    strokeWidth=0
).resolve_scale(color="independent")

# %% [markdown]
# ## FSM analysis

# %%
source = eyfsp_la_2_com_lit_maths_additional_tables_2013_2019.copy()

# %%
source.columns

# %%
base = alt.Chart(
    source[(source.geographic_level == "National") & (source.fsm != "Total")]
)

# %%
base.mark_bar().encode(
    x=alt.X("fsm"),
    y=alt.Y("at_least_expected_percent"),
    facet=alt.Facet("area_of_learning"),
)

# %%
eyfsp_la_1_key_measures_additional_tables_2013_2019[
    eyfsp_la_1_key_measures_additional_tables_2013_2019.characteristic
    == "FSM eligibility"
]

# %%
fsm_2018.head()

# %%
base = alt.Chart(
    fsm_2019[
        (fsm_2019.geographic_level == "National") & (fsm_2019.FSM_GROUP != "Total")
    ]
)

# %%
base.mark_bar().encode(
    x=alt.X("FSM_GROUP"),
    y=alt.Y("emerging_percent"),
    facet=alt.Facet("elg_category", columns=7),
    tooltip=alt.Tooltip(["emerging_percent"]),
)

# %%
base = alt.Chart(fsm_2018[(fsm_2018.level == "National") & (fsm_2018.fsm != "Total")])

# %%
base.mark_bar().encode(
    x=alt.X("fsm"),
    y=alt.Y("emerging_percent:Q"),
    facet=alt.Facet("elg_category", columns=7),
    tooltip=alt.Tooltip(["emerging_percent"]),
)

# %%
ethnicity_fsm_gender_school_readiness.head()

# %%
school_readiness = aps_gld_elg_expr_2013_2019[
    (aps_gld_elg_expr_2013_2019.time_period == 201819)
    & (aps_gld_elg_expr_2013_2019.geographic_level == "National")
    & (aps_gld_elg_expr_2013_2019.gender == "Total")
].gld_percent[0]

# %%
school_readiness

# %%
fsm_gap = pd.melt(
    ethnicity_fsm_gender_school_readiness,
    id_vars=["Ethnicity"],
    value_vars=["Boys_FSM", "Boys_NonFSM", "Girls_FSM", "Girls_NonFSM"],
)

# %%
fsm_gap.rename(columns={"variable": "fsm_gender"}, inplace=True)

# %%
fsm_gap["diff_from_average"] = fsm_gap.value - school_readiness

# %%
sorted_ethnicity = fsm_gap[fsm_gap["fsm_gender"] == "Girls_NonFSM"].sort_values(
    by=["diff_from_average"], ascending=False
)

# %%
chart_fsm_eth_gend = (
    alt.Chart(fsm_gap)
    .mark_circle(size=80)
    .encode(
        x=alt.X("diff_from_average"),
        y=alt.Y("Ethnicity", sort=list(sorted_ethnicity.Ethnicity)),
        color=alt.Color(
            "fsm_gender",
            scale=alt.Scale(
                domain=["Boys_FSM", "Boys_NonFSM", "Girls_FSM", "Girls_NonFSM"],
                range=[
                    nesta_colours[0],
                    nesta_colours[1],
                    nesta_colours[2],
                    nesta_colours[8],
                ],
            ),
        ),
        tooltip=alt.Tooltip(["diff_from_average"]),
    )
)

# %%
chart_fsm_eth_gend.properties(width=400, height=500)

# %%
