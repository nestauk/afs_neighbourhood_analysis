# Data and methodology

## Methodological narrative

Our goal in this project is to identify clusters of local authorities that are similar in a set of background conditions that are useful for explaining differences in their early year outcomes. In follow-up research we will sample these clusters in a survey aimed at understanding early years policies and practices that might explain those differences in outcomes. In addition to this, we are interested in identifying _individual_ local authorities that under or over-perform their cluster's early year outcomes. They could be a useful setting for additional research aimed at explaining those differences.

In order to achieve our goals, we have implemented a "consequential clustering" pipeline where we use an array of indicators about local authorities from the Public Health Outcomes Framework (PHOF) to cluster them into groups. We tune the clustering algorithms with the goal of maximising differences in early year outcomes between clusters (that is the "consequential" outcome we are interested in). This requires a number of steps that we describe in detail in section @sec:method.

## Data sources {#sec:data}

### Early Years Outcomes

For our outcome measure, we are using the [Early Years Foundation Stage Profile](https://www.gov.uk/government/publications/early-years-foundation-stage-profile-handbook) (EYFSP) results.  A statutory assessment developed by the Department for Education, it is conducted at the end of Reception, testing a number of Areas of Learning and, within these, Early Learning Goals. The main domains are summarised below:

1. Communication and language
2. Physical development
3. Personal, social and emotional development
4. Literacy
5. Maths
6. Understanding of the world
7. Expressive arts and design

Whilst we acknowledge the flaws in the EYFSP ([Nursery World](https://www.nurseryworld.co.uk/news/article/eyfs-revisions-muddled-and-inappropriate), [Early Years Educator](https://www.earlyyearseducator.co.uk/features/article/technical-pros-and-cons)), and the changes made to the assessment over time, it is still one of the only outcome measures we have which is publically available and accessible. The [A Fairer Start mission](https://www.nesta.org.uk/fairer-start/) at [Nesta](https://www.nesta.org.uk/) is using the EYFSP as part of its strategy, with their main goal to narrow the gap of those meeting a Good Level of Development in the EYFSP between those children on Free School Meals and those who are not.

Leaving aside the lack of alternatives, EYFSP has further advantages - for example, it is published broken down into a number of categories including:

* Local Authority (LA),
* gender,
* Area of Learning,
* Early Learning Goals,
* ethnicity,
* Special Education Needs and Disabilities (SEND)
* and Free School Meals status.

This makes it possible to consider performance in a variety of outcome areas for various groups e.g. do the same LAs outperform when we look at the overall percentage of children reaching a Good Level of Development vs. percentage of children on Free School Meals?

### Public Health Outcomes Framework

The main source of data we use for clustering is the [Public Health Outcomes Framework](https://fingertips.phe.org.uk/profile/public-health-outcomes-framework) (PHOF), a measurement framework maintained by the Office for Health Improvement and Disparities with the goal to "improve and protect the nation's health, and improve the health of the poorest fastest". The framework contains 180 indicators capturing a wide array of health outcomes, social determinants of health and background sociodemographic information.[^1]

[^1]: We have obtained it through the [Fingertips API](https://fingertips.phe.org.uk/api), which provides programmatic access to a wide range of public health indicators using the [`fingertips_py`](https://fingertips-py.readthedocs.io/en/latest/) Python package.

It is worth noting that we expect strong overlap / correlation between indicators in PHOF (for example, it includes mortality rates from a wide range of diseases) which we will address downstream using dimensionality reduction techniques.

We also emphasise that we have focused our clustering on PHOF data for reasons of convenience. Our goal is not to cluster local authorities based on causal drivers of early year outcomes but to capture different types of local authority that display variation in those outcomes. Insofar the PHOF data indicators act as proxies for other relevant local conditions that are not included in the analysis (such as for example data about the industrial composition of a location, or about its detailed sociodemographic characteristics), it fulfils our purposes.[^2]

[^2]: Having said this, we would expect that incorporating other relevant dimensions of a local authority context in our analysis would improve the quality and usefulness of our clustering. This is an area for further work.

We process the data in the following ways:

1. We remove indicators which are not available at the County / Unitary Authority (C/UA) level at which early year outcomes is released, and with which we want to merge our data.
2. Some of the indicators in PHFO are available by sex, age and other category types. We create a new indicator for each combinations of categories for which it is available (for example, the indicator "16-17 year olds not in education, employment or training (NEET) or whose activity is not known" is split into "16-17 year olds not in education, employment or training (NEET) or whose activity is not known: Female-16-17 yrs", "16-17 year olds not in education, employment or training (NEET) or whose activity is not known: Male-16-17 yrs" and "16-17 year olds not in education, employment or training (NEET) or whose activity is not known: Persons-16-17 yrs".
3. We focus on the latest period for which each indicator was collected. We calculate the z-score for each indicator (for each value of an indicator in a C/UA we remove its mean and divide by its standard deviation so they are all in the same scale).
4. We remove indicators where the percentage of C/UAs with missing data is below 2.5% and then remove a small number of C/UAs that still have missing data in at least one indicator. This includes Rutland, Isles of Scilly and Hammersmith and Fulham. We select this threshold with the goal of balancing indicator breadth versus good coverage of C/UAs. As @fig:complete shows, including indicators with poorer coverage reduces the number of C/UAs that we are able to cluster. The 2.5% of coverage threshold makes it possible for us to cluster most C/UAs using 189 indicators.[^3]

![Trade off between indicator completeness and location completeness in the most recent period. The horizontal axis represents the number of
Us we are able to include in our clustering for a given level of strictness in indicator coverage. The vertical axis represents the number of indicators we are able to include. A threshold of 1 means including all indicators regardless of their coverage, a threshold of 0 means only including indicators with perfect coverage (there are none).](png/missing_strategy.png){#fig:complete}

[^3]: An option to explore further would be to interpolate missing values in order to increase the number of indicators we are able to include for a given number of C/UAs.

### Other secondary data

TO BE ADDED

## Methods {#sec:method}

Our clustering pipeline consists of the following steps:

### Dimensionality reduction

We start with a table with 144 C/UAs which we want to cluster based on their similarities and differences in a 189-dimensional vector. As noted above, we would expect some of these dimensions to be strongly correlated or noisy. We address this by taking two dimensionality reducion steps:

1. We begin with a principal component analysis that extracts the uncorrelated components (linear combinations of indicators) that explain most of the variance in the data. We extract 5, 20, 35, 50, 65 and 80 components (we will choose the optimal number of components based on its ability to generate clusters that maximise differences in early year outcomes across clusters).
2. Having transformed $T_{144,189}$ into $T_{144,K}$ where K is the number of components we extracted, we project each C/UAC/ into a two-dimensional space using UMAP (Uniform Manifold Approximation and Projection for Dimension Reduction), another dimensionality reduction technique that clusters similar observations into a lower-dimensional space [UMAP ref]. This has the goal of segmenting observations in a way that makes it easier to cluster them.

### Robust clustering

Having reduced the dimensionality of our data, we proceed to cluster it. Here, we follow an ensemble clustering procedure aimed at increasing the robustness of our clustering assignment (i.e. the extent to which the clustering is dictated by our choice of clustering algorithm, specific parameters or random initialisations of the algorithm). This consists of the following steps:

1. We cluster our data using three clustering algorithms and combinations of parameters:

- **K-means clustering:** this algorithm places K cluster centroids in the data space randomly, assigns each observation to its closest cluster, recalculates the centroid based on these assignments, and reassigns observations again. This process is repeated for 300 iterations or until the cluster assignments become stable. We run the algorithm for a range of values of K between 20 and 50.
- **Affinity Propagation:** In this algorithm, observations pass messages with each other in order to determine which should be its "exemplar" (the observation that best represents other observations in its group). These exemplars define the clusters. Differently from K-means, this algorithm determines the number of clusters in a data-driven way. The main tuning parameter in this algorithm is damping, which dampens incoming "messages" in order to reduce oscilations in cluster assignments.
- **Gaussian mixture:** This algorithm models the data as a number of latent Gaussian distributions and assigns each observation to the distribution (cluster) most likely to have generated it. We run the algorithm for a range of components between 20 and 50.

2. Each of our combinations of clustering algorithms and parameter sets generates a clustering assignment: each observation is assigned to a cluster. We proceed to build a network where every observation is a node. Every time that two observations are assigned to the same cluster by a clustering algorithm / parameter set, we increase the weight of the connection between those two observations (nodes) by one. This will result in a network where observations that tend to be placed in the same clusters by different clustering algorithms and parameters will have strong connections, and those that are rarely placed in the same clusters will have weak or no connections.
3. We decompose the above network into communities of nodes (observations) that are tightly connected internally and weakly connected externally using the Louvain community detection algorithm [REF]. Each of these communities constitutes a cluster. This algorithm has a resolution parameter that determines the level of granularity in the communities that are extracted from the network. We run the community extraction for a range of resolutions between 0.4 and 1.

### Consequential clustering evaluation

The process above generates a cluster assignment for each combination of tuning parameters (principal components extracted and resolution during community extraction) (there are 70 combinations in total). We want to choose the set of parameters that generates a clustering assignment with the highest level of variation in early year outcomes. We use two strategies to measure this variation:

1. We calculate the silouhette score for each vector of early year outcomes based on the cluster assignments. This captures the extent to which C/UAs in each cluster tend to have similar early year profiles to other C/UAs in the cluster, and different early year profiles to C/UAs in other clusters.
2. For each early year outcome variable that we are considering, we calculate the median score in each cluster and the variance between them. Higher variance suggests a greater degree of dispersion between clusters in their early year outcomes.

### Results of the consequential clustering evaluation

The heatmaps in @fig:diagnostics show the Z-score in our two measures of inter-cluster heterogeneity in early year outcomes for combinations of parameters.[^4] Blue colours indicate a higher degree of heterogeneity, which is desirable. We use this information to select our clustering algorithm, with five extracted components and a community resolution of 0.7.

We note that a small number of components seem to capture most of the variance in the PHF data, suggesting strong correlations between the variables in it. It would be desirable, as a follow-up, to expand the range of indicators we use in our clustering in order to capture more dimensions of a C/UA sociodemographic and economic situation.

[^4]: We use average early year scores to calculate the measure of heterogeneity in variances.

![Consequential evaluation of clustering results under different parameters (number of principal components extracted and community resolution) and measures of cluster disparity in early year outcomes (silouhette score and variance of median scores by cluster). The color of the cells represents the Zscore, with blue representing higher heterogeneity between clusters, and red representing lower heterogeneity between clusters.](png/clustering_diagnostics.png){#fig:diagnostics}
