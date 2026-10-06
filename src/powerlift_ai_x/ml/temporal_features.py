from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


# ============================================================
# EXACT 22-FEATURE PRODUCTION CONTRACT
# ============================================================

CONTEXT_FEATURES = [
    "year",
    "division",
    "weight_class",
    "equipment",
]


HISTORY_FEATURES = [
    "previous_year_count",
    "previous_year",
    "years_since_previous",

    "previous_total",
    "previous_squat",
    "previous_bench",
    "previous_deadlift",
    "previous_bodyweight",

    "historical_mean_total",
    "historical_max_total",
    "historical_min_total",
    "historical_std_total",

    "historical_max_squat",
    "historical_max_bench",
    "historical_max_deadlift",

    "historical_mean_bodyweight",

    "previous_total_change",
    "previous_total_change_pct",
]


PRODUCTION_FEATURES = (
    CONTEXT_FEATURES
    + HISTORY_FEATURES
)


# ============================================================
# ATHLETE-YEAR AGGREGATION
# ============================================================

def build_athlete_year_table(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Reproduce the notebook's exact athlete-year aggregation.
    """

    required = [
        "resolved_athlete_id",
        "year",
        "total",
        "best_squat",
        "best_bench",
        "best_deadlift",
        "bodyweight",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    athlete_year = (
        df[
            required
        ]
        .groupby(
            [
                "resolved_athlete_id",
                "year",
            ],
            as_index=False,
        )
        .agg(
            year_total_mean=(
                "total",
                "mean",
            ),

            year_total_max=(
                "total",
                "max",
            ),

            year_total_min=(
                "total",
                "min",
            ),

            year_best_squat=(
                "best_squat",
                "max",
            ),

            year_best_bench=(
                "best_bench",
                "max",
            ),

            year_best_deadlift=(
                "best_deadlift",
                "max",
            ),

            year_bodyweight_mean=(
                "bodyweight",
                "mean",
            ),
        )
    )

    athlete_year = athlete_year.sort_values(
        [
            "resolved_athlete_id",
            "year",
        ]
    ).reset_index(drop=True)

    return athlete_year


# ============================================================
# TEMPORAL FEATURE CONSTRUCTION
# ============================================================

def build_temporal_features(
    athlete_year: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the exact temporal features used by the ML notebook.

    The current target year is never included in its own
    historical features.
    """

    required = [
        "resolved_athlete_id",
        "year",
        "year_total_mean",
        "year_total_max",
        "year_total_min",
        "year_best_squat",
        "year_best_bench",
        "year_best_deadlift",
        "year_bodyweight_mean",
    ]

    missing = [
        column
        for column in required
        if column not in athlete_year.columns
    ]

    if missing:
        raise ValueError(
            "Missing athlete-year columns: "
            + ", ".join(missing)
        )

    result = athlete_year.copy()

    group = result.groupby(
        "resolved_athlete_id",
        group_keys=False,
    )

    # --------------------------------------------------------
    # PREVIOUS-YEAR FEATURES
    # --------------------------------------------------------

    result["previous_year"] = (
        group["year"].shift(1)
    )

    result["previous_total"] = (
        group["year_total_mean"].shift(1)
    )

    result["previous_squat"] = (
        group["year_best_squat"].shift(1)
    )

    result["previous_bench"] = (
        group["year_best_bench"].shift(1)
    )

    result["previous_deadlift"] = (
        group["year_best_deadlift"].shift(1)
    )

    result["previous_bodyweight"] = (
        group["year_bodyweight_mean"].shift(1)
    )

    result["previous_year_count"] = (
        group.cumcount()
    )

    result["years_since_previous"] = (
        result["year"]
        - result["previous_year"]
    )

    # --------------------------------------------------------
    # HISTORICAL AGGREGATES
    # --------------------------------------------------------

    result["historical_mean_total"] = (
        group["year_total_mean"]
        .transform(
            lambda s:
            s.expanding()
            .mean()
            .shift(1)
        )
    )

    result["historical_max_total"] = (
        group["year_total_max"]
        .transform(
            lambda s:
            s.expanding()
            .max()
            .shift(1)
        )
    )

    result["historical_min_total"] = (
        group["year_total_min"]
        .transform(
            lambda s:
            s.expanding()
            .min()
            .shift(1)
        )
    )

    result["historical_std_total"] = (
        group["year_total_mean"]
        .transform(
            lambda s:
            s.expanding()
            .std()
            .shift(1)
        )
    )

    result["historical_max_squat"] = (
        group["year_best_squat"]
        .transform(
            lambda s:
            s.expanding()
            .max()
            .shift(1)
        )
    )

    result["historical_max_bench"] = (
        group["year_best_bench"]
        .transform(
            lambda s:
            s.expanding()
            .max()
            .shift(1)
        )
    )

    result["historical_max_deadlift"] = (
        group["year_best_deadlift"]
        .transform(
            lambda s:
            s.expanding()
            .max()
            .shift(1)
        )
    )

    result["historical_mean_bodyweight"] = (
        group["year_bodyweight_mean"]
        .transform(
            lambda s:
            s.expanding()
            .mean()
            .shift(1)
        )
    )

    # --------------------------------------------------------
    # PREVIOUS-PERFORMANCE CHANGE
    # --------------------------------------------------------

    result["previous_previous_total"] = (
        group["year_total_mean"].shift(2)
    )

    result["previous_total_change"] = (
        result["previous_total"]
        - result["previous_previous_total"]
    )

    result["previous_total_change_pct"] = (
        result["previous_total_change"]
        / result["previous_previous_total"]
        * 100
    )

    result["previous_total_change_pct"] = (
        result["previous_total_change_pct"]
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
    )

    return result


# ============================================================
# BUILD COMPLETE TEMPORAL DATASET
# ============================================================

def build_temporal_dataset(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Reproduce the notebook's complete temporal dataset.

    Temporal features are calculated at athlete-year level
    and then attached back to every original competition
    record.

    Merge key:
        resolved_athlete_id + year

    This intentionally preserves the original competition-row
    granularity.
    """

    athlete_year = build_athlete_year_table(df)

    temporal = build_temporal_features(
        athlete_year
    )

    temporal_lookup = temporal[
        [
            "resolved_athlete_id",
            "year",
            *HISTORY_FEATURES,
        ]
    ].copy()

    ml_temporal = df.merge(
        temporal_lookup,
        on=[
            "resolved_athlete_id",
            "year",
        ],
        how="left",
        validate="many_to_one",
    )

    # The notebook explicitly verifies this invariant.
    if len(ml_temporal) != len(df):
        raise ValueError(
            "Temporal merge changed the number of "
            "competition records: "
            f"{len(df):,} -> {len(ml_temporal):,}"
        )

    return ml_temporal


# ============================================================
# CREATE SUPERVISED TEMPORAL DATASET
# ============================================================

def build_supervised_temporal_dataset(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the supervised temporal dataset.

    Only competition records with at least one previous
    athlete-year are eligible.
    """

    ml_temporal = build_temporal_dataset(df)

    temporal_ml_df = ml_temporal[
        ml_temporal["previous_year_count"] >= 1
    ].copy()

    return temporal_ml_df


# ============================================================
# EXTRACT EXACT MODEL FEATURES
# ============================================================

def extract_production_features(
    temporal_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Extract the exact 22 production features expected by
    the trained models.

    Context features come directly from the original
    competition row.

    Historical features were attached by
    build_temporal_dataset().
    """

    missing_features = [
        feature
        for feature in PRODUCTION_FEATURES
        if feature not in temporal_df.columns
    ]

    if missing_features:
        raise ValueError(
            "Missing production features: "
            + ", ".join(missing_features)
        )

    return temporal_df[
        PRODUCTION_FEATURES
    ].copy()