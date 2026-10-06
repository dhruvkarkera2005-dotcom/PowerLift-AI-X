from powerlift_ai_x.dataset.statistics import (
    DatasetStatistics,
    NumericStatistics,
    calculate_dataset_statistics,
)
from powerlift_ai_x.models.competition_result import (
    CompetitionResult,
)
from powerlift_ai_x.models.enums import Equipment


def make_result(
    athlete_id="ATH-1",
    competition="Competition A",
    year=2026,
    division="Open",
    weight_class="66",
    equipment=Equipment.CLASSIC,
    bodyweight=65.0,
    squat=220.0,
    bench=135.0,
    deadlift=245.0,
    total=600.0,
):
    return CompetitionResult(
        athlete_id=athlete_id,
        competition=competition,
        year=year,
        division=division,
        weight_class=weight_class,
        equipment=equipment,

        bodyweight=bodyweight,

        squat_1=200.0,
        squat_2=210.0,
        squat_3=squat,
        best_squat=squat,

        bench_1=120.0,
        bench_2=130.0,
        bench_3=bench,
        best_bench=bench,

        deadlift_1=220.0,
        deadlift_2=230.0,
        deadlift_3=deadlift,
        best_deadlift=deadlift,

        total=total,
        place=1,
    )


def test_empty_dataset():
    statistics = calculate_dataset_statistics([])

    assert isinstance(
        statistics,
        DatasetStatistics,
    )

    assert statistics.total_records == 0

    assert statistics.records_by_year == {}
    assert statistics.records_by_competition == {}
    assert statistics.records_by_division == {}
    assert statistics.records_by_weight_class == {}
    assert statistics.records_by_equipment == {}
    assert statistics.athletes_by_record_count == {}

    for field in (
        statistics.bodyweight,
        statistics.best_squat,
        statistics.best_bench,
        statistics.best_deadlift,
        statistics.total,
    ):
        assert isinstance(
            field,
            NumericStatistics,
        )

        assert field.count == 0
        assert field.minimum is None
        assert field.maximum is None
        assert field.average is None


def test_numeric_statistics():
    results = [
        make_result(
            athlete_id="ATH-1",
            bodyweight=60.0,
            squat=200.0,
            bench=100.0,
            deadlift=200.0,
            total=500.0,
        ),
        make_result(
            athlete_id="ATH-2",
            bodyweight=70.0,
            squat=240.0,
            bench=140.0,
            deadlift=260.0,
            total=640.0,
        ),
    ]

    statistics = calculate_dataset_statistics(
        results
    )

    assert statistics.bodyweight.count == 2
    assert statistics.bodyweight.minimum == 60.0
    assert statistics.bodyweight.maximum == 70.0
    assert statistics.bodyweight.average == 65.0

    assert statistics.best_squat.count == 2
    assert statistics.best_squat.minimum == 200.0
    assert statistics.best_squat.maximum == 240.0
    assert statistics.best_squat.average == 220.0

    assert statistics.best_bench.count == 2
    assert statistics.best_bench.minimum == 100.0
    assert statistics.best_bench.maximum == 140.0
    assert statistics.best_bench.average == 120.0

    assert statistics.best_deadlift.count == 2
    assert statistics.best_deadlift.minimum == 200.0
    assert statistics.best_deadlift.maximum == 260.0
    assert statistics.best_deadlift.average == 230.0

    assert statistics.total.count == 2
    assert statistics.total.minimum == 500.0
    assert statistics.total.maximum == 640.0
    assert statistics.total.average == 570.0


def test_metadata_statistics():
    results = [
        make_result(
            athlete_id="ATH-1",
            competition="Competition A",
            year=2025,
            division="Open",
            weight_class="59",
            equipment=Equipment.CLASSIC,
        ),
        make_result(
            athlete_id="ATH-1",
            competition="Competition B",
            year=2026,
            division="Open",
            weight_class="66",
            equipment=Equipment.EQUIPPED,
        ),
        make_result(
            athlete_id="ATH-2",
            competition="Competition A",
            year=2025,
            division="Junior",
            weight_class="59",
            equipment=Equipment.CLASSIC,
        ),
    ]

    statistics = calculate_dataset_statistics(
        results
    )

    assert statistics.total_records == 3

    assert statistics.records_by_year == {
        2025: 2,
        2026: 1,
    }

    assert statistics.records_by_competition == {
        "Competition A": 2,
        "Competition B": 1,
    }

    assert statistics.records_by_division == {
        "Junior": 1,
        "Open": 2,
    }

    assert statistics.records_by_weight_class == {
        "59": 2,
        "66": 1,
    }

    assert statistics.records_by_equipment == {
        "CLASSIC": 2,
        "EQUIPPED": 1,
    }


def test_athlete_record_distribution():
    results = [
        make_result(
            athlete_id="ATH-1"
        ),
        make_result(
            athlete_id="ATH-1"
        ),
        make_result(
            athlete_id="ATH-1"
        ),
        make_result(
            athlete_id="ATH-2"
        ),
        make_result(
            athlete_id="ATH-2"
        ),
        make_result(
            athlete_id="ATH-3"
        ),
    ]

    statistics = calculate_dataset_statistics(
        results
    )

    assert statistics.athletes_by_record_count == {
        1: 1,
        2: 1,
        3: 1,
    }


def test_none_values_are_excluded_from_numeric_statistics():
    result = make_result()

    result.bodyweight = None
    result.best_squat = None
    result.best_bench = None
    result.best_deadlift = None
    result.total = None

    statistics = calculate_dataset_statistics(
        [result]
    )

    assert statistics.bodyweight.count == 0
    assert statistics.best_squat.count == 0
    assert statistics.best_bench.count == 0
    assert statistics.best_deadlift.count == 0
    assert statistics.total.count == 0