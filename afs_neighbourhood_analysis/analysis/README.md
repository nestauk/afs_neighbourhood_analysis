# Summary of analysis pipeline

## 1. Create data

- We are currently working with two core datasets:
  - The Public Health England Public Health Indicator Framework (PHF) obtained via `fingertips_py`
  - A set of EFSYP indicators
- We are working at the "Counties and Unitary activities (CUAs) level at which the EFSYP data is available, and focusing only on England
- See `afs_outperforming_analysis/pipeline/README.md` for additional information about the data collection pipeline.

[TODO]

- We are collecting additional secondary data to boost the clustering
- We could use additional EY indicators to measure outcomes
- We need to fix some issues with changes in area codes in 2021 which mean we are losing a small number of geographies from our analysis.

## 2. Consequential clustering

- We want to use the PHF data to cluster CUAs in a way that is informative about EFSYP performance. In order to do this we implement a pipeline where we grid-search for the clustering parameters that generate the clustering solution with the largest differences between EFSYP outcomes.
- The clustering itself involves the following steps:
  - Dimensionality reduction to combine redundant variables (several indicators in PHF are quasi-duplicated) and projection of CUAs into a 2-d space using UMAP
  - Ensemble clustering where we build a network that connects CUAs based on their co-occurrence in clusters. We then decompose the network using community detection
  - Several parameters here are tuned using the consequential approach (i.e. ability to generate clusters that are distinctive _in their EFSYP outcomes_ based on silouhette scores and variance of EFSYP scores between clusters.
- See `afs_outperforming_analysis/pipeline/lad_clustering/consequential_evaluation.py` for the implementation
- Missingness means that we need to trade-off variable coverage against CUA coverage: we remove variables with _many_ missing values and then CUAs with _any_ missing values. Being less strict in removing variables means having to remove more geographies.

[TODO]

- Explore imputation approaches to deal with missing data in geographies / variables.

## 3. Analysis

Run `afs_outperforming_analysis/analysis/clustering/report_analysis.py` to reproduce all the analysis and produce charts.

This reads a cluster assignment that we undertook separately and yields analyses of...

* Geographic, demographic and secondary differences between clusters
* Early year performance differences between clusters in 2019 and over time
* Outperforming and underperfming areas
* Gender parity in 2019, evolution of differences and out and underperforming areas

All charts are saved in `outputs/figures/`

You can find a write up of the results in `outputs/figures/section_cluster_findings.md`





[TODO]

- Reproduce the analysis with more variables
- Expand the cluster explainability analysis using Shapley values
- Choropleths
- Consider differences in PHF indicators _inside clusters_
- Write up results
