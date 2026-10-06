from powerlift_ai_x.dataset.deduplicator import (
    build_deduplication_report,
    deduplicate_results,
    find_duplicate_groups,
    make_result_key,
)
from powerlift_ai_x.models.competition_result import (
    CompetitionResult,
)
from powerlift_ai_x.models.enums import Equipment


def make_result(
    athlete_id="ATH-1",
    competition="Competition A",
    year=2026,
    weight_class="66",
    total=600.0,
):
    return CompetitionResult(
        athlete_id=athlete_id,
        competition=competition,
        year=year,
        division="Open",
        weight_class=weight_class,
        equipment=Equipment.CLASSIC,
        bodyweight=65.0,
        squat_1=200.0,
        squat_2=210.0,
        squat_3=220.0,
        best_squat=220.0,
        bench_1=120.0,
        bench_2=130.0,
        bench_3=135.0,
        best_bench=135.0,
        deadlift_1=220.0,
        deadlift_2=230.0,
        deadlift_3=245.0,
        best_deadlift=245.0,
        total=total,
        place=1,
    )


def test_make_result_key_is_deterministic():
    result = make_result()

    assert make_result_key(result) == make_result_key(result)


def test_identical_results_are_duplicates():
    result_1 = make_result()
    result_2 = make_result()

    groups = find_duplicate_groups(
        [result_1, result_2]
    )

    assert len(groups) == 1
    assert len(groups[0].records) == 2


def test_same_athlete_different_competitions_are_not_duplicates():
    result_1 = make_result(
        competition="Competition A"
    )

    result_2 = make_result(
        competition="Competition B"
    )

    groups = find_duplicate_groups(
        [result_1, result_2]
    )

    assert groups == []


def test_same_athlete_different_years_are_not_duplicates():
    result_1 = make_result(
        year=2025
    )

    result_2 = make_result(
        year=2026
    )

    groups = find_duplicate_groups(
        [result_1, result_2]
    )

    assert groups == []


def test_report_counts_duplicates():
    result_1 = make_result()
    result_2 = make_result()
    result_3 = make_result(
        athlete_id="ATH-2"
    )

    report = build_deduplication_report(
        [
            result_1,
            result_2,
            result_3,
        ]
    )

    assert report.total_records == 3
    assert report.unique_records == 2
    assert report.duplicate_records == 1
    assert report.duplicate_groups == 1


def test_deduplicate_keeps_first_occurrence():
    result_1 = make_result()
    result_2 = make_result()

    unique = deduplicate_results(
        [result_1, result_2]
    )

    assert len(unique) == 1
    assert unique[0] == result_1


def test_deduplicate_preserves_legitimate_records():
    result_1 = make_result(
        competition="Competition A"
    )

    result_2 = make_result(
        competition="Competition B"
    )

    unique = deduplicate_results(
        [result_1, result_2]
    )

    assert len(unique) == 2