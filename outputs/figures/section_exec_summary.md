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

In this analysis, we are aiming to uncover differences in school readiness outcomes between similar English Counties and Unitary Authorities (C/UAs), trying to determine why certain C/UAs do better or worse than their peers.

We use the Fingertips Public Health England (PHE) Framework as our input dataset to first cluster the C/UAs. The clustering itself was done by running many models with different hyperparameters - those C/UAs that were linked together the most times over the many iterations make up the final clusters. These clusters are based on similar socio-demographic and health factors, with 7 clusters being the final result.

From here, we then looked at the Early Years Foundation Stage Profile (EYFSP) results for these clusters, concentrating on the Average Point Score and the Percentage of Children that reach an Expected Level of Development. We also looked at how these results changed through time, and the gender gap between them.  By comparing within clusters, we can see which C/UAs are "outperforming" relative to the similar C/UAs within their cluster, and which are "underperforming".

Initial results show that their economic, societal and typical drivers of school readiness cannot solely explain the differences in their EYFSP. Whilst it is true for Cluster 0, a cluster made up of wealthy C/UAs in the East and South East of England with high life expectancy, that the known factors of increasing levels of development (children not living in poverty, not having a teenage mother, no incidences of domestic violence) seem to separate the outperformers and underperformers, it does not hold for all the clusters. Clusters 1, 5, 6 and 7 have very similar levels of school readiness but are very different clusters. For example, Cluster 5 consists of the London Boroughs and Cluster 7 consists of rural C/UAs with aging populations. When we looked at the typical factors which lead to good levels of development, there was no clear separation between the outperforming and underperforming C/UAs. In Cluster 6 we even saw two authorities from the Greater Manchester Combined Authority having different results, despite sharing similar policies and services.

What we learned most from our analysis was there is still a lot to do to unpick why certain C/UAs do better than others, and vice versa. We plan to follow this analysis up with more secondary data analysis, including within it industry and population data from [NOMIS](https://www.nomisweb.co.uk/), and environmental factors from the [Access to Healthy Assets and Hazards](https://data.cdrc.ac.uk/dataset/access-healthy-assets-hazards-ahah) data. We also intend to conduct an ambitious survey, piloted with 30 Local Authorities (LAs), we will be asking them to describe their Early Years Policy and Practices to try and understand the more nuanced reasons for the differences between their EYFSP results. Should the pilot be successful, this will be scaled up to all 151 LAs in England, one of the most comprehensive studies of the Early Years work done by councils to date.

