# Summary of analysis pipeline

## 1. Create data

* We are currently working with two core datasets:
  * The Public Health England Public Health Indicator Framework (PHF) obtained via `fingertips_py`
  * A set of EFSYP indicators
* We are working at the "Counties and Unitary activities (CUAs) level at which the EFSYP data is available, and focusing only on England
* See `afs_outperforming_analysis/pipeline/README.md` for additional information about the data collection pipeline.

[TODO]
* We are collecting additional data to boost the clustering
* We still need to fix some issues with area names and codes which mean we are losing a small number of local authorities.

## 2. Consequential clustering

* We want to use the PHF data to cluster CUAs in a way that is informative about EFSYP data. In order to do this we implement a pipeline where we grid-search for the clustering parameters that generate the clustering solution with the largest differences between early year outcomes.
* The clustering itself involves the following steps:
    * Dimensionality reduction to combine redundant variables (several indicators in PHF are quasi-duplicated) and projection of CUAs into a 2-d space using UMAP
    * Ensemble clustering where we build a network that connects CUAs based on their co-occurrence in clusters. We then decompose the network using community detection
    * Several parameters here are tuned using the consequential approach.
* See `afs_outperforming_analysis/pipeline/lad_clustering/consequential_evaluation.py` for the implementation
* Missingness means that we need to trade-off variable coverage against CUA coverage: we remove variables with many missing values and then CUAs with any missing values. Being less strict with variables means having to be more strict with CUAs.

[TODO]
* Explore imputation approaches to deal with missing data

## 3. Analysis

* We use the "best performing" parameter set to extract clusters and analyse the data. So far this includes considering:
  * Differences in EFSYP performance between clusters
  * Evolution of EFSYP permance
  * Differences in Gender gap (Boy/Girl EFSYP in an indicator and area, in all cases <1)  between clusters.
  * Evolution of gender gaps in clusters
  * Differences in fingertips data underpinning clustering outcomes

[TODO]
* Reproduce the analysis with more variables
* Expand the cluster explainability analysis using Shapley values
* Choropleths
* Consider differences in PHF indicators *inside clusters*
* Write up results