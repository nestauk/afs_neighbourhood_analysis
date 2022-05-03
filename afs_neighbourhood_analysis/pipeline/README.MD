# AFS Neighbourhood Analysis Pipeline

## Secondary data

This pipeline collects and processes indicators about the sociodemographic and health characteristics of UK localities using `fingertips_py`, a python wrapper around the NHS API.

It includes the following steps:

### Fetch the data from NHS

This flow collects tables for all indicators and geographies in each measurement framework available from `fingertips_py`. Note the large number of splits - we need to collect data fronm around 1700 unique indicators.

```
python afs_neighbourhood_analysis/pipeline/fingertips/flow.py \
--production \
run \
--max-workers 5 \
--max-num-splits 2000 \
```

### Parse the data from NHS

This flow parses the data. This includes parsing dates and only keeping indicators available at the `district / unitary` level. The data is stored in the flow as a lookup between `framework_id` and the parsed and cleaned dataframe combining all indicators for the framework.

```
python afs_neighbourhood_analysis/pipeline/fingertips/data_parse_flow.py \
--production \
run \
--max-workers 2
```
