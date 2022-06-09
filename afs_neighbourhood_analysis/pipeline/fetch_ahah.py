import pandas as pd
from afs_neighbourhood_analysis.pipeline import read_from_s3
from afs_neighbourhood_analysis.pipeline.preprocess_data import (
    process_ahah_columns,
    change_geographic_level,
)


def create_ahah():
    ahah = read_from_s3.df_from_s3("access_to_healthy_assets_and_hazards/AHAH_V3.csv")

    ahah = (
        ahah.pipe(process_ahah_columns)
        .pipe(
            change_geographic_level,
            conv_from="LSOA11CD",
            conv_to="OA11CD",
            on="LSOA11CD",
        )
        .pipe(
            change_geographic_level,
            conv_from="OA11CD",
            conv_to="CTYUA21CD",
            on="OA11CD",
        )
    )

    return ahah.groupby(["CTYUA21CD", "CTYUA21NM"]).mean().reset_index()
