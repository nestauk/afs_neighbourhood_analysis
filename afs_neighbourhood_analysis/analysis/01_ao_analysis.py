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

# %%
# %load_ext autoreload
# %autoreload 2

# %%
import pandas as pd
import numpy as np
import fingertips_py as ftp
import matplotlib.pyplot as plt
from pandas_profiling import ProfileReport

# %%
import geopandas as gpd

# %%
from afs_neighbourhood_analysis.utils import utils
import altair as alt

## reads in the colours as an array called nesta_colours
colours = utils.load_colours()
for key, val in colours.items():
    if key == "nesta_colours_new":
        nesta_colours = val

## if this doesn't work, check that the Averta font is in the fontbook app on your mac and also turned on (if it says multiple copies installed just ignore it)
alt.themes.register('nestafont', utils.nestafont)
alt.themes.enable('nestafont')

# %%
# Find relevant datasets andd its corresponding keys

phof = ftp.get_profile_by_name('public health outcomes framework')
phof_meta = ftp.get_metadata_for_profile_as_dataframe(phof['Id'])
# Search dataset using keywords 
indicator_meta = phof_meta[phof_meta['Indicator'].str.contains('smoke | School')]

print(indicator_meta['Indicator'].values)
print(indicator_meta['Indicator'].keys) #<- what to use when reading in dataset using the ftp.get_data_for_indicator_at_all_available_geographies(key) function

# %%
## This adds the selection which allows me to select individual LAs.
la_select = alt.selection_multi(fields=["Area Name"])

# %%
# Create geopandas for later location-based maps 
map_df = gpd.read_file('https://opendata.arcgis.com/datasets/244b257482da4778995cf11ff99e9997_0.geojson')

# %% [markdown]
# # 2. Datasets

# %% [markdown]
# ## 2.1 LOW BIRTH RATE

# %%
low_birth_df = ftp.get_data_for_indicator_at_all_available_geographies(20101)

# %%
low_birth_df.head(3)

# %% [markdown]
# ### Geography coverage

# %%
profile = ProfileReport(low_birth_df, title="Pandas Profiling Report")

# %%
profile.to_file("low_birth_rate_profile.html")

# %% [markdown]
# ### Geography coverage

# %%
low_birth_df.columns

# %%
low_birth_df.isnull().sum()

# %%
# Observations of each area for each area code releases (duplicates because of this)
# Codes from Apr 2021 chosen- for districts and counties
low_birth_df['Area Type'].unique()

# %%
years = low_birth_df['Time period'].unique()

# %%
# Create subset dataframes for each year
df_dict_low = {}

for year in years:
#     df_dict[year]['Value'] = df_dict[year]['Count']/df_dict[year]['Denominator']
    df_dict_low[year] = low_birth_df[low_birth_df['Time period'] == year]

# %%
# Number of districts covered per year

for year in years:
    print('{} : {}'.format(year,len(df_dict_low[year][df_dict_low[year]['Area Type'] == 'Districts & UAs (from Apr 2021)']['Area Name'].unique())))

# %%
# Number of counties covered per year

for year in years:
    print('{} : {}'.format(year,len(df_dict_low[year][df_dict_low[year]['Area Type'] == 'Counties & UAs (from Apr 2021)']['Area Name'].unique())))

# %%
# Get observations at county and district level (using codes from Apr 2021)
df_concat_county = pd.concat([v[v['Area Type'] == 'Counties & UAs (from Apr 2021)'] for k,v in df_dict_low.items()])
df_concat_district = pd.concat([v[v['Area Type'] == 'Districts & UAs (from Apr 2021)'] for k,v in df_dict_low.items()])

# %% [markdown]
# PLOT - Percentage of low weight births per year by county

# %%
piv = pd.pivot_table(df_concat_county, values="Value",index=["Area Name"], columns=["Time period"], fill_value=0)

fig, ax = plt.subplots(figsize = (20,60))
im = ax.imshow(piv, cmap="Greens")
fig.colorbar(im, ax=ax, shrink= 0.5)

ax.set_xticks(range(len(piv.columns)))
ax.set_yticks(range(len(piv.index)))
ax.set_xticklabels(piv.columns, rotation=90)
ax.set_yticklabels(piv.index)
ax.set_xlabel("Year")
ax.set_ylabel("County")

plt.tight_layout()
plt.savefig("./low_birth_weight_county.png")
plt.show()

# %% [markdown]
# PLOT - Percentage of low weight births per year by district

# %%
piv = pd.pivot_table(df_concat_district, values="Value",index=["Area Name"], columns=["Time period"], fill_value=0)

fig, ax = plt.subplots(figsize = (20,60))
im = ax.imshow(piv, cmap="Greens")
fig.colorbar(im, ax=ax, shrink= 0.3)

ax.set_xticks(range(len(piv.columns)))
ax.set_yticks(range(len(piv.index)))
ax.set_xticklabels(piv.columns, rotation=90)
ax.set_yticklabels(piv.index)
ax.set_xlabel("Year")
ax.set_ylabel("District")
ax.set_title("")

plt.tight_layout()
plt.savefig("./low_birth_weight_district.png")
plt.show()

# %% [markdown]
# PLOT - 20 LAD (district) with highest proption of births at low birth birth weight

# %%
df_low_2020 = df_concat_district[df_concat_district['Time period']==2020]
bar_chart_highest_weight = (
    alt.Chart(df_low_2020.sort_values(
        by="Value", ascending=False)[:20])).mark_bar(
    color="#18A48C").encode(
    y=alt.Y('Area Name',sort=alt.EncodingSortField(
        "Value", op='sum',order='descending'),
            title='LAD Region'), x=alt.X(f"Value", title="20 LAD with the highest proportion of births at low birth weight")).add_selection(
    la_select).properties(height=250,width=300)

# %%
bar_chart_highest_weight

# %%
# Note: Isles of Scilly & City of London and hence -2 to -22 to ignore these values
bar_chart_lowest_weight = (
    alt.Chart(df_low_2020.sort_values(
        by="Value", ascending=False)[-22:])).mark_bar(
    color="#18A48C").encode(
    y=alt.Y('Area Name',sort=alt.EncodingSortField(
        "Value", op='sum',order='ascending'),
            title='LAD Region'), x=alt.X(f"Value", title="20 LAD with the lowest proportion of births at low birth weight")).add_selection(
    la_select).properties(height=250,width=300)

# %%
bar_chart_lowest_weight

# %% [markdown]
# ## SMOKING IN EARLY PREGNANCY

# %%
smoking_df = ftp.get_data_for_indicator_at_all_available_geographies(93579)

# %%
smoking_df.head(3)

# %%
smoking_df.columns

# %%
smoking_df.isnull().sum()

# %%
for col in smoking_df.columns:
    print('{} : {}'.format(col,smoking_df[col].unique()))

# %%
# Only available at one year - 2018/19
smoking_df['Time period'].unique()

# %%
# Observations of each area for each area code releases (duplicates because of this)
# Codes from Apr 2021 chosen- for counties
smoking_df['Area Type'].unique()

# %%
# Get observations at county level (using codes from Apr 2021)
smoking_df_ = smoking_df[smoking_df['Area Type'] == 'Counties & UAs (from Apr 2021)']
smoking_df__ = smoking_df_[['Area Name', 'Area Code', 'Value']]

# %% [markdown]
# Create geopands and join geo to data

# %%
merged_smoking = map_df.set_index('CTYUA21CD').join(smoking_df__.set_index('Area Code')).reset_index()


# %%
merged_smoking

# %%
london_boroughs = ['City of London',
'Barking and Dagenham',
'Barnet',
'Bexley',
'Brent',
'Bromley',
'Camden',
'Croydon',
'Ealing',
'Enfield',
'Greenwich',
'Hackney',
'Hammersmith and Fulham',
'Haringey',
'Harrow',
'Havering',
'Hillingdon',
'Hounslow',
'Islington',
'Kensington and Chelsea',
'Kingston upon Thames',
'Lambeth',
'Lewisham',
'Merton',
'Newham',
'Redbridge',
'Richmond upon Thames',
'Southwark',
'Sutton',
'Tower Hamlets',
'Waltham Forest',
'Wandsworth',
'Westminster']

# %%
# Create list of London borough codes for London map 
london_codes = list(merged_smoking[merged_smoking['Area Name'].isin(london_boroughs)]['CTYUA21CD'])

# %% [markdown]
# PLOT - Percentage of mothers smoking during early pregnancy by county

# %%
# [Following is Rcahel's code adapted]
## So this is the code I used to bin my percentage data which enabled me to have a choropleth map with a discrete colour scale rather than a continuous one. I'll highlight what you'd need to change to have a continuous one though!

bins = [0, 5, 10, 15, 20, 25, 30]
labels=["0-5", "5-10", "10-15","15-20", "20-25","25-30"]

merged_smoking["binned_percent"] = pd.cut(merged_smoking['Value'], bins, labels=labels)

## As I mentioned, sometimes my geodataframes stop being geodataframes and I have *no* idea why so this bit of code is to make sure it definitely is! If it's not a geodataframe altair will throw up the error message "Object is not JSON serialisable"

merge_data_to_plot = gpd.GeoDataFrame(merged_smoking, geometry="geometry")

## In order to create the custom colour palette corresponding to the bins above I define the variables here (if you find a nicer colour palette please let me know :P)
domain = labels
range_ = ['#2A2B2A', "#5E4955", "#996888",'#C99DA3', "#C6DDF0", '#759FBC']

## This adds the selection in which allows me to select individual LAs.
la_select = alt.selection_multi(fields=["la_name"])

## This adds a condition to the colour variable based on the selection criteria above. So if nothing is selected the colour is based on the binned_gld_percent variable (:N means that it's a categorical named variable, if I used gld_percent which isn't binned and added :Q, this is where the colour scheme would change to continuous)

## Also note the domain and range_ that I defined above being used here. The alt.value is the colour that the other LAs go when one is selected.
color = alt.condition(la_select,
                  alt.Color('binned_percent:N',
                  scale=alt.Scale(domain=domain, range=range_)),
                  alt.value('lightgray')) 

## I have separated out London from the rest of the country because the London boroughs are too small! I can send you the .csv I used which just has a list of only London boroughs and their codes.

## This code will plot the choropleth map, color is defined above and is coloured by binned_gld_percent, the tooltip adds another interactive element which allows people to hover over the LA and it will give them the LA name and the gld_percent (this time the actual number rather than the binned number).

choro_gld_no_london = alt.Chart(merge_data_to_plot[~merge_data_to_plot['CTYUA21CD'].isin(london_codes
                                                                                    )], title="Percentage of mothers smoking during early pregnancy by county").mark_geoshape(
    stroke='black'
).encode( 
    color=color, 
    tooltip=[alt.Tooltip("Area Name:N", title="LA"), 
        alt.Tooltip("Value:Q", title= "Average GLD (%)", format="1.2f")]
).add_selection(
        la_select
    ).properties(width=500, height=600)

# %%
## this is very similar code but for the London boroughs
choro_gld_london = alt.Chart(merge_data_to_plot[merge_data_to_plot['CTYUA21CD'].isin(london_codes)]).mark_geoshape(
    stroke='black'
).encode( 
    color=color, 
    tooltip=[alt.Tooltip("Area Name:N", title="LA"), 
        alt.Tooltip("Value:Q", title= "Average GLD (%)", format="1.2f")]
).add_selection(
        la_select
    ).properties(width=300, height=250)

# %%
bar_chart_highest = (
    alt.Chart(smoking_df__.sort_values(
        by="Value", ascending=False)[:20])).mark_bar(color="#18A48C").encode(
    y=alt.Y('Area Name',sort=alt.EncodingSortField(
        "Value", op='sum',order='descending'), title='LAD Region'), x=alt.X(
        f"Value", title="LAD with the highest percentage of mothers smoking during early pregnancy ready children")).add_selection(
    la_select).properties(height=250,width=300)

# %%
map_and_bar_ldn = alt.vconcat(bar_chart_highest, choro_gld_london).resolve_scale(color="independent")
alt.hconcat(choro_gld_no_london, map_and_bar_ldn).configure_view(strokeWidth=0).resolve_scale(color="independent")

# %%
