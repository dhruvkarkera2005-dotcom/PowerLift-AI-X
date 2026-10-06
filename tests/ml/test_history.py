from powerlift_ai_x.ml.history import (
    AthleteHistoryExample,
    build_athlete_history_examples,
    history_example_to_dict,
)


def make_row(
    athlete_id,
    year,
    competition,
    squat,
    bench,
    deadlift,
    total,
    bodyweight,
):
    return {
        "athlete_id": athlete_id,
        "competition": competition,
        "year": year,
        "division": "Open",
        "weight_class": "74",
        "equipment": "CLASSIC",
        "bodyweight": bodyweight,
        "squat_1": squat[0],
        "squat_2": squat[1],
        "squat_3": squat[2],
        "best_squat": squat[3],
        "bench_1": bench[0],
        "bench_2": bench[1],
        "bench_3": bench[2],
        "best_bench": bench[3],
        "deadlift_1": deadlift[0],
        "deadlift_2": deadlift[1],
        "deadlift_3": deadlift[2],
        "best_deadlift": deadlift[3],
        "total": total,
    }


def test_first_competition_does_not_create_example():
    rows = [
        make_row(
            "ATH-1",
            2022,
            "Competition A",
            (200.0, 210.0, 220.0, 210.0),
            (110.0, 120.0, 130.0, 120.0),
            (220.0, 230.0, 240.0, 230.0),
            560.0,
            72.0,
        )
    ]

    examples = build_athlete_history_examples(rows)

    assert examples == []


def test_second_competition_uses_first_as_history():
    rows = [
        make_row(
            "ATH-1",
            2022,
            "Competition A",
            (200.0, 210.0, 220.0, 210.0),
            (110.0, 120.0, 130.0, 120.0),
            (220.0, 230.0, 240.0, 230.0),
            560.0,
            72.0,
        ),
        make_row(
            "ATH-1",
            2023,
            "Competition B",
            (220.0, 230.0, 240.0, 230.0),
            (120.0, 130.0, 140.0, 130.0),
            (230.0, 250.0, 270.0, 250.0),
            610.0,
            73.0,
        ),
    ]

    examples = build_athlete_history_examples(rows)

    assert len(examples) == 1

    example = examples[0]

    assert isinstance(
        example,
        AthleteHistoryExample,
    )

    assert example.athlete_id == "ATH-1"
    assert example.target_year == 2023
    assert (
        example.target_competition
        == "Competition B"
    )

    assert (
        example.features.previous_competition_count
        == 1
    )

    assert example.features.previous is not None

    assert (
        example.features.previous.squat_1
        == 200.0
    )

    assert (
        example.features.previous.bench_3
        == 130.0
    )

    assert (
        example.features.previous.deadlift_3
        == 240.0
    )

    assert example.target.best_squat == 230.0
    assert example.target.best_bench == 130.0
    assert example.target.best_deadlift == 250.0
    assert example.target.total == 610.0


def test_third_competition_uses_first_two_competitions():
    rows = [
        make_row(
            "ATH-1",
            2021,
            "Competition A",
            (190.0, 200.0, 210.0, 200.0),
            (100.0, 110.0, 120.0, 110.0),
            (210.0, 220.0, 230.0, 220.0),
            530.0,
            71.0,
        ),
        make_row(
            "ATH-1",
            2022,
            "Competition B",
            (200.0, 210.0, 220.0, 210.0),
            (110.0, 120.0, 130.0, 120.0),
            (220.0, 230.0, 240.0, 230.0),
            560.0,
            72.0,
        ),
        make_row(
            "ATH-1",
            2023,
            "Competition C",
            (220.0, 230.0, 240.0, 230.0),
            (120.0, 130.0, 140.0, 130.0),
            (230.0, 250.0, 270.0, 250.0),
            610.0,
            73.0,
        ),
    ]

    examples = build_athlete_history_examples(rows)

    assert len(examples) == 2

    second = examples[0]
    third = examples[1]

    assert (
        second.features.previous_competition_count
        == 1
    )

    assert (
        third.features.previous_competition_count
        == 2
    )

    assert (
        third.features.historical_best_total
        == 560.0
    )


def test_multiple_athletes_are_processed_independently():
    rows = [
        make_row(
            "ATH-B",
            2022,
            "Competition B",
            (200.0, 210.0, 220.0, 210.0),
            (110.0, 120.0, 130.0, 120.0),
            (220.0, 230.0, 240.0, 230.0),
            560.0,
            72.0,
        ),
        make_row(
            "ATH-A",
            2022,
            "Competition A",
            (180.0, 190.0, 200.0, 190.0),
            (100.0, 110.0, 120.0, 110.0),
            (200.0, 210.0, 220.0, 210.0),
            510.0,
            70.0,
        ),
        make_row(
            "ATH-B",
            2023,
            "Competition C",
            (220.0, 230.0, 240.0, 230.0),
            (120.0, 130.0, 140.0, 130.0),
            (230.0, 250.0, 270.0, 250.0),
            610.0,
            73.0,
        ),
        make_row(
            "ATH-A",
            2023,
            "Competition D",
            (200.0, 210.0, 220.0, 210.0),
            (110.0, 120.0, 130.0, 120.0),
            (210.0, 230.0, 240.0, 230.0),
            560.0,
            71.0,
        ),
    ]

    examples = build_athlete_history_examples(rows)

    assert len(examples) == 2

    assert examples[0].athlete_id == "ATH-A"
    assert examples[1].athlete_id == "ATH-B"

    assert (
        examples[0]
        .features
        .previous
        .total
        == 510.0
    )

    assert (
        examples[1]
        .features
        .previous
        .total
        == 560.0
    )


def test_input_order_does_not_change_result():
    row_a = make_row(
        "ATH-1",
        2022,
        "Competition A",
        (200.0, 210.0, 220.0, 210.0),
        (110.0, 120.0, 130.0, 120.0),
        (220.0, 230.0, 240.0, 230.0),
        560.0,
        72.0,
    )

    row_b = make_row(
        "ATH-1",
        2023,
        "Competition B",
        (220.0, 230.0, 240.0, 230.0),
        (120.0, 130.0, 140.0, 130.0),
        (230.0, 250.0, 270.0, 250.0),
        610.0,
        73.0,
    )

    first = build_athlete_history_examples(
        [row_a, row_b]
    )

    second = build_athlete_history_examples(
        [row_b, row_a]
    )

    assert first == second


def test_target_values_do_not_enter_history():
    history_row = make_row(
        "ATH-1",
        2022,
        "Competition A",
        (200.0, 210.0, 220.0, 210.0),
        (110.0, 120.0, 130.0, 120.0),
        (220.0, 230.0, 240.0, 230.0),
        560.0,
        72.0,
    )

    target_row = make_row(
        "ATH-1",
        2023,
        "Competition B",
        (400.0, 410.0, 420.0, 410.0),
        (300.0, 310.0, 320.0, 310.0),
        (450.0, 460.0, 470.0, 460.0),
        1180.0,
        80.0,
    )

    examples = build_athlete_history_examples(
        [target_row, history_row]
    )

    assert len(examples) == 1

    example = examples[0]

    assert (
        example.features.historical_best_total
        == 560.0
    )

    assert (
        example.features.historical_best_total
        != target_row["total"]
    )


def test_history_example_to_dict():
    rows = [
        make_row(
            "ATH-1",
            2022,
            "Competition A",
            (200.0, 210.0, 220.0, 210.0),
            (110.0, 120.0, 130.0, 120.0),
            (220.0, 230.0, 240.0, 230.0),
            560.0,
            72.0,
        ),
        make_row(
            "ATH-1",
            2023,
            "Competition B",
            (220.0, 230.0, 240.0, 230.0),
            (120.0, 130.0, 140.0, 130.0),
            (230.0, 250.0, 270.0, 250.0),
            610.0,
            73.0,
        ),
    ]

    examples = build_athlete_history_examples(rows)

    result = history_example_to_dict(
        examples[0]
    )

    assert result["athlete_id"] == "ATH-1"
    assert result["target_year"] == 2023
    assert (
        result["target_competition"]
        == "Competition B"
    )

    assert (
        result["features"]
        ["previous_competition_count"]
        == 1
    )

    assert (
        result["features"]
        ["previous"]
        ["squat_1"]
        == 200.0
    )

    assert (
        result["target"]
        ["best_squat"]
        == 230.0
    )


def test_missing_year_is_rejected():
    row = make_row(
        "ATH-1",
        2023,
        "Competition A",
        (200.0, 210.0, 220.0, 210.0),
        (110.0, 120.0, 130.0, 120.0),
        (220.0, 230.0, 240.0, 230.0),
        560.0,
        72.0,
    )

    del row["year"]

    try:
        build_athlete_history_examples([row])
    except ValueError as exc:
        assert "year" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_missing_athlete_id_is_rejected():
    row = make_row(
        "ATH-1",
        2023,
        "Competition A",
        (200.0, 210.0, 220.0, 210.0),
        (110.0, 120.0, 130.0, 120.0),
        (220.0, 230.0, 240.0, 230.0),
        560.0,
        72.0,
    )

    del row["athlete_id"]

    try:
        build_athlete_history_examples([row])
    except ValueError as exc:
        assert "athlete_id" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )