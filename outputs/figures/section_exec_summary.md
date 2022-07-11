---
title: "Mapping differences in early year outcomes in England"
subtitle: "A clustering approach"
author:
    - "Juan Mateos-Garcia"
    - "Rachel Wilcock"
    - "Adeola Otubusen"
date:
    - July 2022
figPrefix:
  - "Figure"
  - "Figures"
tblPrefix:
  - "Table"
  - "Tables"
secPrefix:
  - "Section"
  - "Sections"
number_sections: True
---

# Executive summary

In this report we use unsupervised machine learning methods to cluster English Counties and United Authorities (C/UAs), compare their school readiness outcomes, and try to identify C/UAs that perform or outperform on those indicators compared to their peers.

We use the Fingertips Public Health England (PHE) Framework as our input dataset to cluster the C/UAs. We tune our clustering algorithms to maximise difference in early year outcomes between clusters, and to ensure a robust assignment of C/UAs to clustesrs. This approach yields 8 clusters.

From here, we look at the Early Years Foundation Stage Profile (EYFSP) results for these clusters, concentrating on the Average Point Score and the Percentage of Children that reach an Expected Level of Development. We also look at how these results change over time, and the gender gap between them.  By comparing within clusters, we can see which C/UAs are "outperforming" relative to the similar C/UAs within their cluster, and which are "underperforming".

Initial results suggest that C/UAs economic, societal and typical drivers of school readiness cannot solely explain the differences in their EYFSP. Whilst we do find that in Cluster 0, composed of wealthy C/UAs in the East and South East of England with high life expectancy, known drivers of improved child development (such as children not living in poverty, not having a teenage mother, no incidences of domestic violence) seem to separate the outperformers and underperformers, this does not hold in several other clusters. Clusters 1, 5, 6 and 7 present very different contexts but similar levels of school readiness. For example, Cluster 5 consists of the London Boroughs and Cluster 7 consists of rural C/UAs with aging populations. When we look at the typical factors which lead to good levels of development, there is no clear separation between the outperforming and underperforming C/UAs in those clusters. In Cluster 6 we even see two authorities from the Greater Manchester Combined Authority with different results despite similarities in policies and services.

These results suggest that there is much work left to do to understand why certain C/UAs outperform / underperform others. In order to do this, we are incorporating more secondary data into our analysis, including economic and population data from [NOMIS](https://www.nomisweb.co.uk/), and environmental factors from the [Access to Healthy Assets and Hazards](https://data.cdrc.ac.uk/dataset/access-healthy-assets-hazards-ahah) data. We also intend to conduct an ambitious survey, piloted with 30 Local Authorities (LAs), to collect data about  their Early Years Policy and Practices which might underpin the differences we have evidenced here. If that pilot is successful, this will scaled up data collection to all 151 LAs in England in one of the most comprehensive studies of local early years policy performed to date.

