from metaflow import current, FlowSpec, Parameter, project, step
from typing import Dict, List, Union


@project(name="afs_neighbourhood_analysis")
class ParseIndicators(FlowSpec):
    """Parses fingertips indicators

    Attributes:
        framework_tables: lookup between framework and indicators
        framework_clean_dfs: lookup between framework and clean dfs
    """

    test_mode = Parameter("test-mode", help="run as test", default=True)

    @step
    def start(self):
        """Starts the flow by reading the raw data"""
        from afs_neighbourhood_analysis.utils.metaflow import get_run

        self.framework_tables = get_run("HealthIndicators").data.framework_tables

        if self.test_mode is True and current.is_production is False:
            self.frameworks = [
                f for f, t in self.framework_tables.items() if len(t) > 0
            ][:3]
        else:
            self.frameworks = [
                f for f, t in self.framework_tables.items() if len(t) > 0
            ]

        self.next(self.parse_tables, foreach="frameworks")

    @step
    def parse_tables(self):
        """For each framework, parse the data"""
        from pandas import concat
        from toolz import pipe
        from afs_neighbourhood_analysis.analysis.fingertips.load_eda import (
            parse_health_indicators,
        )

        self.frame_df_lookup = {
            self.input: (
                pipe(self.framework_tables[self.input], concat, parse_health_indicators)
            )
        }
        self.next(self.join_tables)

    @step
    def join_tables(self, inputs):
        """Joins the tables"""

        self.framework_clean_dfs = {
            k: v for input in inputs for k, v in input.frame_df_lookup.items()
        }

        self.next(self.end)

    @step
    def end(self):
        """No op"""


if __name__ == "__main__":
    ParseIndicators()
