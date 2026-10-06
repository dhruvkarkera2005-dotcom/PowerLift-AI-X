from powerlift_ai_x.dataset.profiler import (
    DatasetProfile,
    profile_dataset,
)
from powerlift_ai_x.models.competition_result import (
    CompetitionResult,
)
from powerlift_ai_x.models.enums import (
    Equipment,
)


def make_result(
    athlete_id: str,
    competition: str = "Test Competition",
    year: int = 2026,
    division: str = "Open",
    weight_class: str = "66",
    equipment: Equipment = Equipment.CLASSIC,
    squat=(200.0, 210.0, -220.0),
    bench=(120.0, -130.0, 135.0),
    deadlift=(220.0, 230.0, 240.0),
    total=585.0,
) -> CompetitionResult:

    return CompetitionResult(
        athlete_id=athlete_id,
        competition=competition,
        year=year,
        division=division,
        weight_class=weight_class,
        equipment=equipment,

        bodyweight=65.0,

        squat_1=squat[0],
        squat_2=squat[1],
        squat_3=squat[2],
        best_squat=(
            max(
                value
                for value in squat
                if value is not None
                and value > 0
            )
            if any(
                value is not None and value > 0
                for value in squat
            )
            else None
        ),

        bench_1=bench[0],
        bench_2=bench[1],
        bench_3=bench[2],
        best_bench=(
            max(
                value
                for value in bench
                if value is not None
                and value > 0
            )
            if any(
                value is not None and value > 0
                for value in bench
            )
            else None
        ),

        deadlift_1=deadlift[0],
        deadlift_2=deadlift[1],
        deadlift_3=deadlift[2],
        best_deadlift=(
            max(
                value
                for value in deadlift
                if value is not None
                and value > 0
            )
            if any(
                value is not None and value > 0
                for value in deadlift
            )
            else None
        ),

        total=total,
        place=1,
    )


def test_profile_empty_dataset():
    profile = profile_dataset([])

    assert isinstance(
        profile,
        DatasetProfile,
    )

    assert profile.total_records == 0
    assert profile.unique_athletes == 0
    assert profile.competitions == 0
    assert profile.years == 0
    assert profile.divisions == 0
    assert profile.weight_classes == 0

    assert profile.equipment == {}

    assert profile.squat_missing == 0
    assert profile.squat_valid == 0
    assert profile.squat_failed_attempts == 0

    assert profile.bench_missing == 0
    assert profile.bench_valid == 0
    assert profile.bench_failed_attempts == 0

    assert profile.deadlift_missing == 0
    assert profile.deadlift_valid == 0
    assert profile.deadlift_failed_attempts == 0

    assert profile.total_missing == 0
    assert profile.total_valid == 0


def test_profile_counts_metadata():
    results = [
        make_result(
            "ATH-1",
            competition="Competition A",
            year=2025,
            division="Open",
            weight_class="59",
            equipment=Equipment.CLASSIC,
        ),
        make_result(
            "ATH-2",
            competition="Competition B",
            year=2026,
            division="Junior",
            weight_class="66",
            equipment=Equipment.EQUIPPED,
        ),
        make_result(
            "ATH-1",
            competition="Competition A",
            year=2025,
            division="Open",
            weight_class="59",
            equipment=Equipment.CLASSIC,
        ),
    ]

    profile = profile_dataset(results)

    assert profile.total_records == 3
    assert profile.unique_athletes == 2
    assert profile.competitions == 2
    assert profile.years == 2
    assert profile.divisions == 2
    assert profile.weight_classes == 2

    assert profile.equipment == {
        "CLASSIC": 2,
        "EQUIPPED": 1,
    }


def test_profile_counts_failed_attempts():
    result = make_result(
        "ATH-1",
        squat=(200.0, -210.0, -220.0),
        bench=(120.0, -130.0, 135.0),
        deadlift=(220.0, 230.0, -240.0),
    )

    profile = profile_dataset([result])

    assert profile.squat_failed_attempts == 2
    assert profile.bench_failed_attempts == 1
    assert profile.deadlift_failed_attempts == 1


def test_profile_counts_missing_values():
    result = make_result(
        "ATH-1",
        squat=(None, None, None),
        bench=(None, None, None),
        deadlift=(None, None, None),
        total=None,
    )

    # Explicitly remove the derived BEST values.
    result.best_squat = None
    result.best_bench = None
    result.best_deadlift = None

    profile = profile_dataset([result])

    assert profile.squat_missing == 1
    assert profile.squat_valid == 0

    assert profile.bench_missing == 1
    assert profile.bench_valid == 0

    assert profile.deadlift_missing == 1
    assert profile.deadlift_valid == 0

    assert profile.total_missing == 1
    assert profile.total_valid == 0