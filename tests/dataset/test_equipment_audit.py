from powerlift_ai_x.dataset.equipment_audit import (
    audit_equipment,
    unknown_equipment_rows,
)
from powerlift_ai_x.models.competition_result import (
    CompetitionResult,
)
from powerlift_ai_x.models.enums import Equipment


def make_result(
    athlete_id="ATH-1",
    competition="Competition A",
    year=2026,
    equipment=Equipment.CLASSIC,
):
    return CompetitionResult(
        athlete_id=athlete_id,
        competition=competition,
        year=year,
        division="Open",
        weight_class="66",
        equipment=equipment,
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
        total=600.0,
        place=1,
    )


def test_empty_audit():
    report = audit_equipment([])

    assert report.total_records == 0
    assert report.classic_records == 0
    assert report.equipped_records == 0
    assert report.unknown_records == 0
    assert report.competitions_with_unknown == 0
    assert report.rows == ()


def test_audit_counts_equipment():
    results = [
        make_result(
            athlete_id="ATH-1",
            equipment=Equipment.CLASSIC,
        ),
        make_result(
            athlete_id="ATH-2",
            equipment=Equipment.CLASSIC,
        ),
        make_result(
            athlete_id="ATH-3",
            equipment=Equipment.EQUIPPED,
        ),
        make_result(
            athlete_id="ATH-4",
            equipment=Equipment.UNKNOWN,
        ),
    ]

    report = audit_equipment(results)

    assert report.total_records == 4
    assert report.classic_records == 2
    assert report.equipped_records == 1
    assert report.unknown_records == 1
    assert report.competitions_with_unknown == 1


def test_audit_separates_competitions_and_years():
    results = [
        make_result(
            athlete_id="ATH-1",
            competition="Competition A",
            year=2025,
            equipment=Equipment.UNKNOWN,
        ),
        make_result(
            athlete_id="ATH-2",
            competition="Competition A",
            year=2025,
            equipment=Equipment.CLASSIC,
        ),
        make_result(
            athlete_id="ATH-3",
            competition="Competition B",
            year=2026,
            equipment=Equipment.EQUIPPED,
        ),
    ]

    report = audit_equipment(results)

    assert len(report.rows) == 2

    first = report.rows[0]
    second = report.rows[1]

    assert first.competition == "Competition A"
    assert first.year == 2025
    assert first.classic == 1
    assert first.equipped == 0
    assert first.unknown == 1
    assert first.total == 2

    assert second.competition == "Competition B"
    assert second.year == 2026
    assert second.classic == 0
    assert second.equipped == 1
    assert second.unknown == 0
    assert second.total == 1


def test_unknown_equipment_rows():
    classic = make_result(
        athlete_id="ATH-1",
        equipment=Equipment.CLASSIC,
    )

    unknown_1 = make_result(
        athlete_id="ATH-2",
        equipment=Equipment.UNKNOWN,
    )

    unknown_2 = make_result(
        athlete_id="ATH-3",
        equipment=Equipment.UNKNOWN,
    )

    results = [
        classic,
        unknown_1,
        unknown_2,
    ]

    unknown = unknown_equipment_rows(
        results
    )

    assert len(unknown) == 2
    assert unknown[0] == unknown_1
    assert unknown[1] == unknown_2


def test_audit_does_not_modify_results():
    result = make_result(
        equipment=Equipment.UNKNOWN
    )

    original_equipment = result.equipment

    audit_equipment([result])

    assert result.equipment == original_equipment