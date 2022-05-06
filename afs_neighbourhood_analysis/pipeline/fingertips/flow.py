from typing import Dict, List

from metaflow import current, FlowSpec, Parameter, project, step
from toolz import pipe


@project(name="afs_neighbourhood_analysis")
class HealthIndicators(FlowSpec):
    """
    Fetch public health indicators by measurement framework

    Attributes:
        test_mode: if we are running as a test
        framework_ids: ids for frameworks we want to collect
        indicator_ids: ids for indicators we want to collect
        indicator_tables: dict with a key for each indicator
    """

    test_mode: bool
    framework_ids: Dict
    indicator_ids: List
    indicator_tables: Dict
    framework_tables: Dict

    test_mode = Parameter("test-mode", help="running in test mode", default=True)

    @step
    def start(self):
        """Start the flow by
        reading the indicator ids that we need to collect"""

        from fingertips_py import get_all_profiles

        self.framework_ids = [fr["Id"] for fr in get_all_profiles()]

        self.next(self.fetch_indicator_ids)

    @step
    def fetch_indicator_ids(self):
        """Create list of ids and fetch tables for each framework"""
        from fingertips_py import get_metadata_for_profile_as_dataframe
        from itertools import chain

        # This is a lookup between framework_ids and the indicators they contain
        self.framework_metadata = {
            _id: get_metadata_for_profile_as_dataframe(_id)
            for _id in self.framework_ids
        }

        # This gives us the list of ids to collect data from for each framework
        if self.test_mode is True and not current.is_production:

            self.indicator_ids = pipe(
                chain.from_iterable(
                    [
                        framework["Indicator ID"].tolist()
                        for framework in self.framework_metadata.values()
                    ]
                ),
                set,
                list,
            )[
                :3
            ]  # The test only collects the first three indicators
        else:
            self.indicator_ids = pipe(
                chain.from_iterable(
                    [
                        framework["Indicator ID"].tolist()
                        for framework in self.framework_metadata.values()
                    ]
                ),
                set,
                list,
            )

        self.next(self.fetch_tables, foreach="indicator_ids")

    @step
    def fetch_tables(self):
        """Fetch indicator table"""

        # Robust fetch table tries to catch exceptions before they
        # break the flow
        from utils import robust_fetch_table

        self.table = {self.input: robust_fetch_table(self.input)}

        self.next(self.join_indicators)

    @step
    def join_indicators(self, inputs):
        """Joins all indicators in a framework"""

        from utils import clean_fingertips_table

        # Lookup between indicator ids and tables
        self.indicator_tables = {
            key: clean_fingertips_table(value)
            for input in inputs
            for key, value in input.table.items()
        }

        self.next(self.end)

    @step
    def end(self):
        """Create dict lookup between framework ids and indicator tables"""
        from fingertips_py import (
            get_metadata_for_profile_as_dataframe,
            get_all_profiles,
        )

        framework_ids = [fr["Id"] for fr in get_all_profiles()]

        framework_indicator_lookup = {
            _id: set(
                get_metadata_for_profile_as_dataframe(_id)["Indicator ID"].tolist()
            )
            for _id in framework_ids
        }

        # Lookup between framework ids and a list of its indicators

        self.framework_tables = {
            frame_id: [
                t
                for _id, t in self.indicator_tables.items()
                if _id in framework_indicator_lookup[frame_id]
            ]
            for frame_id in framework_indicator_lookup.keys()
        }


if __name__ == "__main__":
    HealthIndicators()
