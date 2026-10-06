from __future__ import annotations

import pandas as pd

from app.logic.competition_data import generate_competition_data
from app.logic.competition_engine import (
    get_category_recommendation,
    get_competitors,
    get_gap_analysis,
    get_podium_threshold,
)


def test_synthetic_data_is_deterministic():
    first = generate_competition_data()
    second = generate_competition_data()

    pd.testing.assert_frame_equal(first, second)


def test_synthetic_data_has_required_columns():
    df = generate_competition_data()

    expected = {
        "category",
        "meet_tier",
        "name",
        "total_kg",
        "wilks_or_gl",
        "placing",
        "year",
    }

    assert expected.issubset(df.columns)


def test_synthetic_data_has_multiple_categories():
    df = generate_competition_data()

    assert df["category"].nunique() >= 2


def test_synthetic_data_has_multiple_tiers():
    df = generate_competition_data()

    assert df["meet_tier"].nunique() >= 2


def test_synthetic_data_has_at_least_three_years():
    df = generate_competition_data()

    assert df["year"].nunique() >= 3


def test_get_competitors_returns_dataframe():
    result = get_competitors(
        category="Men 83 kg",
        meet_tier="National",
        year=2026,
    )

    assert isinstance(result, pd.DataFrame)


def test_get_competitors_has_required_columns():
    result = get_competitors(
        category="Men 83 kg",
        meet_tier="National",
        year=2026,
    )

    expected = {
        "name",
        "total_kg",
        "wilks_or_gl",
        "placing",
        "year",
    }

    assert expected.issubset(result.columns)


def test_get_competitors_is_sorted_by_total():
    result = get_competitors(
        category="Men 83 kg",
        meet_tier="National",
        year=2026,
    )

    totals = result["total_kg"].tolist()

    assert totals == sorted(totals, reverse=True)


def test_podium_threshold_has_three_positions():
    result = get_podium_threshold(
        category="Men 83 kg",
        meet_tier="National",
        target_year=2027,
    )

    assert {
        "gold",
        "silver",
        "bronze",
    }.issubset(result)


def test_podium_threshold_is_ordered():
    result = get_podium_threshold(
        category="Men 83 kg",
        meet_tier="National",
        target_year=2027,
    )

    assert result["gold"] >= result["silver"]
    assert result["silver"] >= result["bronze"]


def test_podium_threshold_contains_history():
    result = get_podium_threshold(
        category="Men 83 kg",
        meet_tier="National",
        target_year=2027,
    )

    assert "history" in result
    assert len(result["history"]) >= 3


def test_podium_threshold_contains_trend():
    result = get_podium_threshold(
        category="Men 83 kg",
        meet_tier="National",
        target_year=2027,
    )

    assert result["trend"] in {
        "rising",
        "flat",
        "falling",
    }


def test_gap_analysis_calculates_current_total():
    lifts = {
        "squat": 250.0,
        "bench": 150.0,
        "deadlift": 260.0,
    }

    threshold = {
        "gold": 700.0,
        "silver": 675.0,
        "bronze": 650.0,
    }

    result = get_gap_analysis(
        lifts,
        threshold,
    )

    assert result["current_total"] == 660.0


def test_gap_analysis_identifies_podium_gap():
    lifts = {
        "squat": 240.0,
        "bench": 140.0,
        "deadlift": 250.0,
    }

    threshold = {
        "gold": 700.0,
        "silver": 675.0,
        "bronze": 650.0,
    }

    result = get_gap_analysis(
        lifts,
        threshold,
    )

    assert result["total_gap_kg"] == 20.0


def test_gap_analysis_returns_per_lift_analysis():
    lifts = {
        "squat": 240.0,
        "bench": 140.0,
        "deadlift": 250.0,
    }

    threshold = {
        "gold": 700.0,
        "silver": 675.0,
        "bronze": 650.0,
    }

    result = get_gap_analysis(
        lifts,
        threshold,
    )

    assert set(result["per_lift_gap"]) == {
        "squat",
        "bench",
        "deadlift",
    }


def test_gap_analysis_returns_priority_lift():
    lifts = {
        "squat": 240.0,
        "bench": 140.0,
        "deadlift": 250.0,
    }

    threshold = {
        "gold": 700.0,
        "silver": 675.0,
        "bronze": 650.0,
    }

    result = get_gap_analysis(
        lifts,
        threshold,
    )

    assert result["priority_lift"] in {
        "squat",
        "bench",
        "deadlift",
    }


def test_category_recommendation_returns_expected_keys():
    lifts = {
        "squat": 250.0,
        "bench": 150.0,
        "deadlift": 260.0,
    }

    result = get_category_recommendation(
        lifts,
        current_bodyweight=82.0,
    )

    assert {
        "current_category",
        "recommended_category",
        "reason",
        "podium_threshold_difference_kg",
    }.issubset(result)


def test_category_recommendation_returns_string_categories():
    lifts = {
        "squat": 250.0,
        "bench": 150.0,
        "deadlift": 260.0,
    }

    result = get_category_recommendation(
        lifts,
        current_bodyweight=82.0,
    )

    assert isinstance(
        result["current_category"],
        str,
    )

    assert isinstance(
        result["recommended_category"],
        str,
    )


def test_category_recommendation_returns_numeric_difference():
    lifts = {
        "squat": 250.0,
        "bench": 150.0,
        "deadlift": 260.0,
    }

    result = get_category_recommendation(
        lifts,
        current_bodyweight=82.0,
    )

    assert isinstance(
        result["podium_threshold_difference_kg"],
        float,
    )