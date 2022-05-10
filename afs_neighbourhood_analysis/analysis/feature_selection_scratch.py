# Script with useful functions for downstream analyses

import logging
import re
from functools import partial
from itertools import product

import altair as alt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import grangercausalitytests
from toolz import pipe


from afs_neighbourhood_analysis.getters.early_years_scores_eyfsp import (
    get_edu_dataframes,
)
from fingertips_py import (
    get_metadata_for_profile_as_dataframe,
)

from afs_neighbourhood_analysis import PROJECT_DIR

EY_VARS_KEEP = [
    "time_period",
    "geographic_level",
    "new_la_code",
    "la_name",
    "gender",
    "average_point_score",
    "elg_percent",
    "gld_percent",
    "comm_lang_lit_percent",
]

GEND = ["Total", "Girls", "Boys"]


def get_year_from_period(period: int) -> int:
    """Extract the last year from a period"""

    return pipe(period, str, lambda string: f"20{string[-2:]}", int)


def parse_ey_table(table: pd.DataFrame) -> pd.DataFrame:
    """
    Parses an early year table.
    """

    return (
        table.filter(items=EY_VARS_KEEP)
        .assign(year=lambda df: df["time_period"].apply(get_year_from_period))
        .query("geographic_level == 'Local Authority'")
        .drop(axis=1, labels=["time_period", "geographic_level"])
        .melt(
            id_vars=["new_la_code", "la_name", "year", "gender"],
            var_name="indicator",
            value_name="score",
        )
    )


def el_goals() -> pd.DataFrame:
    """Read generic early year goals table for local authorities.

    Variables:
        region_code: local authority code
        year: last year in the period e.g. 2019 covers 2018/2019
        gender: group for which an indicator has been calculated
        indicator:
            average_point_score: average total score in 7 early year goals
                in the group (score = 1-3 with 2 = expected)
            elg_percent: percentage achieving expected scores
            gld_percent: percentage wiht a good level of development
                i.e. achieved or expected in a subset of the
                goals including communication, physical and social
                development and literacy and mathematics
            comm_lang_lit_percent: percentage with a good level
                of development in communicatin / language / literacy (?)

    Returns:
        tidy dataframe

    """

    return pipe(get_edu_dataframes()["ELG_GLD"], parse_ey_table)


def public_health_framework():
    """Read public health framework indicators"""

    return (
        pd.read_csv(f"{PROJECT_DIR}/inputs/data/public_health_profile.csv")
        .query("area_type=='Districts & UAs (from Apr 2021)'")
        .reset_index(drop=True)
    )


def make_integrated_table(ey_wide, fingertips, lag, ey_y=2019):
    """Merges an indicator table with a lagged fingertips indicators table"""
    return (
        fingertips.query(f"last_year=={ey_y-lag}")
        .pivot_table(
            index="area_code", columns="indicator_name_expanded", values="value"
        )
        .merge(ey_wide, left_on="area_code", right_on="new_la_code")
    )


def high_corr_vars(corr_table: pd.DataFrame, thres=0.25) -> pd.DataFrame:
    """Returns high correlation indicators"""

    return pipe(
        corr_table,
        lambda table: table.groupby("variable")["value"].median(),
        partial(get_high_low, thres=thres),
    )


def get_high_low(series, thres):
    """Gets the highest and lowest values in a series"""

    ranges = np.arange(0, 1.1, thres)
    return pipe(
        series,
        partial(pd.qcut, q=ranges, labels=False),
        lambda table: (table.reset_index(name="position")),
        lambda table: (
            table.loc[
                table["position"].isin(
                    [list(ranges).index(0), list(ranges).index(ranges[-1]) - 1]
                )
            ]
            .reset_index(drop=True)
            .sort_values("position", ascending=False)
        ),
    )


def calc_corr(
    ey_df: pd.DataFrame, ey_ind: str, fingertips: pd.DataFrame, lags: int, ey_y=2019
):
    """Calculates correlations between a ey indicator
    and fingertips indicators up to a number of lags"""

    ey_wide = (
        ey_df.query(f"indicator == '{ey_ind}'")
        .query(f"year == {ey_y}")
        .pivot(index="new_la_code", columns="gender", values="score")
        .reset_index(drop=False)
    )

    results = []

    for lag in range(0, lags):

        results.append(
            make_integrated_table(ey_wide, fingertips, lag)
            .corr()
            .loc[GEND]
            .assign(indicator=ey_ind)
            .assign(lag=lag)
            .reset_index(drop=False)
            .rename(columns={"index": "gender"})
            .drop(axis=1, labels=GEND)
            .melt(id_vars=["gender", "indicator", "lag"])
        )

    return pd.concat(results)


def plot_corr_results(table):

    return (
        alt.Chart(aps_corr)
        .mark_point(filled=True)
        .encode(
            y=alt.Y(
                "variable",
                sort=alt.EncodingSortField("value", "mean", order="descending"),
                axis=alt.Axis(labels=False, ticks=False),
            ),
            x="value",
            shape="gender",
            tooltip=["variable"],
            color=alt.Color("lag", scale=alt.Scale(scheme="reds")),
        )
        .properties(width=300, height=600)
    )


def make_regression_table(
    ey_df: pd.DataFrame, ey_ind: str, fingertips: pd.DataFrame, lag: int, ey_y=2019
):
    """Calculates correlations between a ey indicator and fingertips
    indicators up to a number of lags"""

    ey_wide = (
        ey_df.query(f"indicator == '{ey_ind}'")
        .query(f"year == {ey_y}")
        .pivot(index="new_la_code", columns="gender", values="score")
        .reset_index(drop=False)
    )

    return make_integrated_table(ey_wide, fingertips, lag)


def remove_missing(int_table: pd.DataFrame, share: float = 0.05):
    """This function removes variables with a high share of missing lads and
    for the rest, missing LADs
    """

    thres = len(int_table) * share

    keep_vars = (
        int_table.isna()
        .sum(axis=0)
        .reset_index(name="missing_n")
        .query(f"missing_n < {thres}")
        .reset_index(drop=True)["index"]
        .tolist()
    )

    return int_table[keep_vars].dropna(axis=0)


def fit_lasso(reg_table, gender):
    """Fit LASSO model"""

    endog = reg_table[gender]
    exog = sm.add_constant(reg_table.drop(axis=1, labels=GEND + ["new_la_code"]))

    print(len(exog))
    print(len(endog))

    lasso = sm.regression.linear_model.OLS(exog=exog, endog=endog)

    return lasso.fit_regularized(method="sqrt_lasso", refit=True, zero_tol=0.05)


def granger_indicator(table, indicator):
    """Calculate granger causality between "total" average point score
    and an indicator
    """

    results = []

    for predictor in table["indicator_name_expanded"].unique():
        print(predictor)

        predictor_results = {}

        for area in table["area_code"].unique():
            predictor_results[area] = {}

            ts = (
                table.query(f"area_code=='{area}'")
                .query(f"indicator_name_expanded=='{predictor}'")
                .query("gender=='Total'")
                .reset_index(drop=True)[["score", "value"]]
            )
            try:
                gr = grangercausalitytests(ts, maxlag=1, verbose=False)
                predictor_results[area]["f_test"] = gr[1][0]["ssr_ftest"][1]
                predictor_results[area]["coeff"] = gr[1][1][1].params[1]

            except:
                predictor_results[area]["f_test"] = np.nan
                predictor_results[area]["coeff"] = np.nan

        results.append(
            pd.DataFrame(predictor_results)
            .T.assign(predictor=predictor)
            .assign(indicator=indicator)
        )
    return results


# %%
def granger_distribution(merged_table, indicator):
    """Calculates granger causality between an indicator and all fingertips variables"""

    return pipe(
        merged_table,
        lambda table: table.query(f"indicator=='{indicator}'"),
        partial(granger_indicator, indicator=indicator),
        list,
        pd.concat,
    )


if __name__ == "__main__":

    elg = el_goals()

    ey_indicators = elg["indicator"].unique()

    pub_health_df = public_health_framework()

    pub_health_proc = (
        pub_health_df.assign(
            indicator_name_expanded=lambda df: [
                name + "-" + sex for name, sex in zip(df["indicator_name"], df["sex"])
            ]
        )
        .assign(
            indicator_name_expanded=lambda df: [
                name + "-" + category if pd.isnull(category) is False else name
                for name, category in zip(df["indicator_name_expanded"], df["category"])
            ]
        )
        .assign(
            indicator_name_expanded=lambda df: [
                re.sub("'", "", name) for name in df["indicator_name_expanded"]
            ]
        )
    )

    logging.info("Correlation analysis")
    aps_corr = calc_corr(elg, "average_point_score", pub_health_proc, 5)

    pipe(calc_corr(elg, "comm_lang_lit_percent", pub_health_proc, 5), plot_corr_results)

    high_corr_vars = pd.concat(
        [
            pipe(
                calc_corr(elg, variable, pub_health_proc, 5),
                partial(high_corr_vars, thres=0.25),
            ).assign(indicator=variable)
            for variable in ey_indicators
        ]
    ).reset_index(drop=True)

    logging.info("Regression analysis")
    reg_table_all = remove_missing(
        make_regression_table(elg, "average_point_score", pub_health_proc, lag=0)
    )

    lasso = fit_lasso(reg_table_all, "Total")

    logging.info("Granger causality")
    all_merged = elg.merge(
        pub_health_proc[
            [
                "indicator_id",
                "area_code",
                "last_year",
                "value",
                "indicator_name_expanded",
            ]
        ],
        left_on=["new_la_code", "year"],
        right_on=["area_code", "last_year"],
    )

    logging.info("Granger causality")
    granger_distr = granger_distribution(all_merged, "average_point_score")
