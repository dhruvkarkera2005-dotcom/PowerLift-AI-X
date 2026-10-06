
from powerlift_ai_x.ml.target import (
    TARGET_FIELDS,
    NextCompetitionTarget,
    extract_next_competition_target,
    target_is_complete,
    target_to_dict,
)


def test_extract_next_competition_target():
    row = {
        "best_squat": 250.0,
        "best_bench": 150.0,
        "best_deadlift": 270.0,
        "total": 670.0,
    }

    target = extract_next_competition_target(
        row
    )

    assert target == NextCompetitionTarget(
        best_squat=250.0,
        best_bench=150.0,
        best_deadlift=270.0,
        total=670.0,
    )


def test_target_preserves_missing_values():
    row = {
        "best_squat": 250.0,
        "best_bench": None,
        "best_deadlift": 270.0,
        "total": None,
    }

    target = extract_next_competition_target(
        row
    )

    assert target.best_squat == 250.0
    assert target.best_bench is None
    assert target.best_deadlift == 270.0
    assert target.total is None


def test_complete_target():
    target = NextCompetitionTarget(
        best_squat=250.0,
        best_bench=150.0,
        best_deadlift=270.0,
        total=670.0,
    )

    assert target_is_complete(target)


def test_incomplete_target():
    target = NextCompetitionTarget(
        best_squat=250.0,
        best_bench=None,
        best_deadlift=270.0,
        total=None,
    )

    assert not target_is_complete(target)


def test_target_to_dict():
    target = NextCompetitionTarget(
        best_squat=250.0,
        best_bench=150.0,
        best_deadlift=270.0,
        total=670.0,
    )

    assert target_to_dict(target) == {
        "best_squat": 250.0,
        "best_bench": 150.0,
        "best_deadlift": 270.0,
        "total": 670.0,
    }


def test_target_fields_are_fixed():
    assert (
        TARGET_FIELDS
        == (
            "best_squat",
            "best_bench",
            "best_deadlift",
            "total",
        )
    )