from powerlift_ai_x.ml.features import (
    ATTEMPT_FIELDS,
    BEST_FIELDS,
    HistoricalFeatures,
    PreviousCompetition,
    build_historical_features,
    features_to_dict,
    previous_competition_to_dict,
)


def make_row(
    year,
    squat,
    bench,
    deadlift,
    total,
    bodyweight,
):
    return {
        "athlete_id": "ATH-1",
        "competition": f"Competition {year}",
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


def test_empty_history():
    features = build_historical_features([])

    assert features == HistoricalFeatures(
        previous_competition_count=0,
        previous=None,
        historical_best_squat=None,
        historical_best_bench=None,
        historical_best_deadlift=None,
        historical_best_total=None,
        historical_best_squat_attempt=None,
        historical_best_bench_attempt=None,
        historical_best_deadlift_attempt=None,
    )


def test_previous_competition_preserves_all_nine_attempts():
    history = [
        make_row(
            2023,
            (210.0, 220.0, 230.0, 220.0),
            (130.0, 140.0, 150.0, 140.0),
            (230.0, 250.0, 270.0, 250.0),
            610.0,
            73.5,
        )
    ]

    features = build_historical_features(history)

    assert features.previous is not None

    assert features.previous.squat_1 == 210.0
    assert features.previous.squat_2 == 220.0
    assert features.previous.squat_3 == 230.0
    assert features.previous.best_squat == 220.0

    assert features.previous.bench_1 == 130.0
    assert features.previous.bench_2 == 140.0
    assert features.previous.bench_3 == 150.0
    assert features.previous.best_bench == 140.0

    assert features.previous.deadlift_1 == 230.0
    assert features.previous.deadlift_2 == 250.0
    assert features.previous.deadlift_3 == 270.0
    assert features.previous.best_deadlift == 250.0

    assert features.previous.total == 610.0
    assert features.previous.bodyweight == 73.5


def test_latest_previous_competition_is_preserved():
    history = [
        make_row(
            2022,
            (200.0, 210.0, 220.0, 210.0),
            (120.0, 125.0, 130.0, 125.0),
            (220.0, 230.0, 240.0, 230.0),
            565.0,
            72.0,
        ),
        make_row(
            2023,
            (220.0, 230.0, 240.0, 230.0),
            (130.0, 140.0, 150.0, 140.0),
            (240.0, 260.0, 280.0, 260.0),
            630.0,
            73.0,
        ),
    ]

    features = build_historical_features(history)

    assert features.previous_competition_count == 2
    assert features.previous is not None

    assert features.previous.squat_1 == 220.0
    assert features.previous.best_squat == 230.0

    assert features.previous.bench_1 == 130.0
    assert features.previous.best_bench == 140.0

    assert features.previous.deadlift_1 == 240.0
    assert features.previous.best_deadlift == 260.0

    assert features.previous.total == 630.0
    assert features.previous.bodyweight == 73.0


def test_historical_best_values_use_all_previous_competitions():
    history = [
        make_row(
            2022,
            (220.0, 230.0, 240.0, 230.0),
            (120.0, 130.0, 140.0, 130.0),
            (240.0, 250.0, 260.0, 250.0),
            610.0,
            72.0,
        ),
        make_row(
            2023,
            (210.0, 220.0, 230.0, 220.0),
            (130.0, 140.0, 150.0, 140.0),
            (250.0, 270.0, 280.0, 270.0),
            630.0,
            73.0,
        ),
    ]

    features = build_historical_features(history)

    assert features.historical_best_squat == 230.0
    assert features.historical_best_bench == 140.0
    assert features.historical_best_deadlift == 270.0
    assert features.historical_best_total == 630.0


def test_all_nine_attempts_are_available_for_historical_attempt_features():
    history = [
        make_row(
            2022,
            (200.0, 210.0, 220.0, 210.0),
            (110.0, 120.0, 130.0, 120.0),
            (220.0, 240.0, 260.0, 240.0),
            570.0,
            72.0,
        ),
        make_row(
            2023,
            (210.0, 220.0, 230.0, 220.0),
            (120.0, 130.0, 140.0, 130.0),
            (230.0, 250.0, 270.0, 250.0),
            600.0,
            73.0,
        ),
    ]

    features = build_historical_features(history)

    assert features.historical_best_squat_attempt == 230.0
    assert features.historical_best_bench_attempt == 140.0
    assert features.historical_best_deadlift_attempt == 270.0


def test_missing_attempts_are_preserved():
    history = [
        make_row(
            2023,
            (200.0, None, None, 200.0),
            (None, 0.0, 0.0, 0.0),
            (None, None, None, None),
            None,
            72.0,
        )
    ]

    features = build_historical_features(history)

    assert features.previous is not None

    assert features.previous.squat_1 == 200.0
    assert features.previous.squat_2 is None
    assert features.previous.squat_3 is None

    assert features.previous.bench_1 is None
    assert features.previous.bench_2 == 0.0
    assert features.previous.bench_3 == 0.0
    assert features.previous.best_bench == 0.0

    assert features.previous.deadlift_1 is None
    assert features.previous.deadlift_2 is None
    assert features.previous.deadlift_3 is None
    assert features.previous.best_deadlift is None

    assert features.previous.total is None


def test_target_record_is_not_used():
    history = [
        make_row(
            2023,
            (200.0, 210.0, 220.0, 210.0),
            (120.0, 130.0, 140.0, 130.0),
            (220.0, 240.0, 260.0, 240.0),
            580.0,
            72.0,
        )
    ]

    target = make_row(
        2024,
        (300.0, 310.0, 320.0, 310.0),
        (200.0, 210.0, 220.0, 210.0),
        (350.0, 360.0, 370.0, 360.0),
        880.0,
        74.0,
    )

    features = build_historical_features(history)

    assert features.previous_competition_count == 1
    assert features.historical_best_squat == 210.0
    assert features.historical_best_bench == 130.0
    assert features.historical_best_deadlift == 240.0
    assert features.historical_best_total == 580.0

    assert features.historical_best_squat != target["best_squat"]
    assert features.historical_best_bench != target["best_bench"]
    assert features.historical_best_deadlift != target["best_deadlift"]
    assert features.historical_best_total != target["total"]


def test_feature_constants_cover_all_attempts():
    assert ATTEMPT_FIELDS == (
        "squat_1",
        "squat_2",
        "squat_3",
        "bench_1",
        "bench_2",
        "bench_3",
        "deadlift_1",
        "deadlift_2",
        "deadlift_3",
    )

    assert BEST_FIELDS == (
        "best_squat",
        "best_bench",
        "best_deadlift",
    )


def test_previous_competition_to_dict():
    previous = PreviousCompetition(
        squat_1=200.0,
        squat_2=210.0,
        squat_3=220.0,
        best_squat=210.0,
        bench_1=120.0,
        bench_2=130.0,
        bench_3=140.0,
        best_bench=130.0,
        deadlift_1=220.0,
        deadlift_2=240.0,
        deadlift_3=260.0,
        best_deadlift=240.0,
        total=580.0,
        bodyweight=72.0,
    )

    assert previous_competition_to_dict(previous) == {
        "squat_1": 200.0,
        "squat_2": 210.0,
        "squat_3": 220.0,
        "best_squat": 210.0,
        "bench_1": 120.0,
        "bench_2": 130.0,
        "bench_3": 140.0,
        "best_bench": 130.0,
        "deadlift_1": 220.0,
        "deadlift_2": 240.0,
        "deadlift_3": 260.0,
        "best_deadlift": 240.0,
        "total": 580.0,
        "bodyweight": 72.0,
    }


def test_features_to_dict():
    history = [
        make_row(
            2023,
            (210.0, 220.0, 230.0, 220.0),
            (130.0, 140.0, 150.0, 140.0),
            (230.0, 250.0, 270.0, 250.0),
            610.0,
            73.5,
        )
    ]

    features = build_historical_features(history)
    result = features_to_dict(features)

    assert result["previous_competition_count"] == 1
    assert result["previous"]["squat_1"] == 210.0
    assert result["previous"]["bench_2"] == 140.0
    assert result["previous"]["deadlift_3"] == 270.0
    assert result["previous"]["total"] == 610.0
    assert result["previous"]["bodyweight"] == 73.5