from typing import Dict, List

from metaflow import current, FlowSpec, Parameter, project, step


@project(name="afs_neighbourhood_analysis")
class PublicHealthIndicators(FlowSpec):
    """
    Fetch public health indicators

    Attributes:
        test_mode: if we are running as a test
        indicator_ids: ids for indicators we want to collect
        indicator_tables: dict with a key for each indicator
    """

    test_mode: bool
    indicator_ids: List
    indicator_tables: Dict

    test_mode = Parameter("test-mode", help="running in test mode", default=True)

    @step
    def start(self):
        """Read the indicator ids that we need to collect"""

        from fingertips_py import get_metadata_for_profile_as_dataframe

        if self.test_mode is True and not current.is_production:
            self.indicator_ids = get_metadata_for_profile_as_dataframe(19)[
                "Indicator ID"
            ].tolist()[:3]
        else:
            self.indicator_ids = get_metadata_for_profile_as_dataframe(19)[
                "Indicator ID"
            ].tolist()

        self.next(self.fetch_table, foreach="indicator_ids")

    @step
    def fetch_table(self):
        """Fetch indicator table"""

        from fingertips_py import get_data_for_indicator_at_all_available_geographies

        self.table = {
            self.input: get_data_for_indicator_at_all_available_geographies(self.input)
        }

        self.next(self.join_results)

    @step
    def join_results(self, inputs):
        """Merges results"""

        from utils import clean_fingertips_table

        self.indicator_tables = {
            indicator_id: clean_fingertips_table(table)
            for input in inputs
            for indicator_id, table in input.table.items()
        }

        self.next(self.end)

    @step
    def end(self):
        """No op"""


if __name__ == "__main__":
    PublicHealthIndicators()
