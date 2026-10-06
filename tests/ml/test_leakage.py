from powerlift_ai_x.ml.leakage import (
    audit_examples_against_rows,
)


def make_row(
    athlete_id,
    year,
    competition,
    squat,
    bench,
    deadlift,
    total,
):
    return {
        "athlete_id": athlete_id,
        "competition": competition,
        "year": year,
        "division": "Open",
        "weight_class": "74",
        "equipment": "CLASSIC",
        "bodyweight": 73.0,
        "squat_1": squat - 10.0,
        "squat_2": squat,
        "squat_3": squat + 5.0,
        "best_squat": squat,
        "bench_1": bench - 5.0,
        "bench_2": bench,
        "bench_3": bench + 5.0,
        "best_bench": bench,
        "deadlift_1": deadlift - 10.0,
        "deadlift_2": deadlift,
        "deadlift_3": deadlift + 5.0,
        "best_deadlift": deadlift,
        "total": total,
    }


def test_generated_examples_have_no_future_years():
    rows = [
        make_row(
            "ATH-1",
            2021,
            "Competition A",
            200.0,
            120.0,
            220.0,
            540.0,
        ),
        make_row(
            "ATH-1",
            2022,
            "Competition B",
            210.0,
            125.0,
            230.0,
            565.0,
        ),
        make_row(
            "ATH-1",
            2023,
            "Competition C",
            220.0,
            130.0,
            240.0,
            590.0,
        ),
    ]

    from powerlift_ai_x.ml.history import (
        build_athlete_history_examples,
    )

    examples = build_athlete_history_examples(rows)

    audit = audit_examples_against_rows(
        rows,
        examples,
    )

    assert audit.total_examples == 2
    assert audit.examples_with_future_year_in_history == 0
    assert audit.examples_with_target_in_history == 0
    assert audit.athlete_ordering_violations == 0
    assert audit.passed


def test_target_competition_is_not_in_history():
    rows = [
        make_row(
            "ATH-1",
            2022,
            "Competition A",
            200.0,
            120.0,
            220.0,
            540.0,
        ),
        make_row(
            "ATH-1",
            2023,
            "Competition B",
            220.0,
            130.0,
            240.0,
            590.0,
        ),
    ]

    from powerlift_ai_x.ml.history import (
        build_athlete_history_examples,
    )

    examples = build_athlete_history_examples(rows)

    audit = audit_examples_against_rows(
        rows,
        examples,
    )

    assert audit.examples_with_target_in_history == 0
    assert audit.passed


def test_multiple_athletes_are_audited_independently():
    rows = [
        make_row(
            "ATH-A",
            2022,
            "Competition A",
            200.0,
            120.0,
            220.0,
            540.0,
        ),
        make_row(
            "ATH-A",
            2023,
            "Competition B",
            210.0,
            125.0,
            230.0,
            565.0,
        ),
        make_row(
            "ATH-B",
            2021,
            "Competition C",
            180.0,
            100.0,
            200.0,
            480.0,
        ),
        make_row(
            "ATH-B",
            2022,
            "Competition D",
            190.0,
            110.0,
            210.0,
            510.0,
        ),
    ]

    from powerlift_ai_x.ml.history import (
        build_athlete_history_examples,
    )

    examples = build_athlete_history_examples(rows)

    audit = audit_examples_against_rows(
        rows,
        examples,
    )

    assert audit.total_examples == 2
    assert audit.passed


def test_same_year_competitions_are_deterministic():
    rows = [
        make_row(
            "ATH-1",
            2023,
            "Competition B",
            220.0,
            130.0,
            240.0,
            590.0,
        ),
        make_row(
            "ATH-1",
            2023,
            "Competition A",
            200.0,
            120.0,
            220.0,
            540.0,
        ),
        make_row(
            "ATH-1",
            2024,
            "Competition C",
            230.0,
            135.0,
            250.0,
            615.0,
        ),
    ]

    from powerlift_ai_x.ml.history import (
        build_athlete_history_examples,
    )

    examples = build_athlete_history_examples(rows)

    audit = audit_examples_against_rows(
        rows,
        examples,
    )

    assert audit.total_examples == 2
    assert audit.passed


def test_audit_reports_bad_target_reference():
    rows = [
        make_row(
            "ATH-1",
            2022,
            "Competition A",
            200.0,
            120.0,
            220.0,
            540.0,
        ),
    ]

    from powerlift_ai_x.ml.history import (
        AthleteHistoryExample,
    )
    from powerlift_ai_x.ml.features import (
        build_historical_features,
    )
    from powerlift_ai_x.ml.target import (
        extract_next_competition_target,
    )

    features = build_historical_features([])

    target = extract_next_competition_target(
        rows[0]
    )

    bad_example = AthleteHistoryExample(
        athlete_id="ATH-1",
        target_year=2022,
        target_competition="Does Not Exist",
        features=features,
        target=target,
    )

    audit = audit_examples_against_rows(
        rows,
        [bad_example],
    )

    assert audit.total_examples == 1
    assert audit.examples_with_target_in_history == 1
    assert not audit.passed