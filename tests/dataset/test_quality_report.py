import json
from pathlib import Path

from powerlift_ai_x.dataset.quality_report import (
    build_quality_report,
    write_quality_report,
)
from powerlift_ai_x.models.competition_result import (
    CompetitionResult,
)
from powerlift_ai_x.models.enums import Equipment


def make_result(
    athlete_id="ATH-1",
    equipment=Equipment.CLASSIC,
    total=600.0,
):
    return CompetitionResult(
        athlete_id=athlete_id,
        competition="Competition A",
        year=2026,
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
        total=total,
        place=1,
    )


def test_build_quality_report_empty():
    report = build_quality_report([])

    assert report["dataset"]["total_records"] == 0

    assert report["equipment"] == {
        "classic": 0,
        "equipped": 0,
        "unknown": 0,
    }

    assert report["integrity"] == {
        "records_with_issues": 0,
        "total_issues": 0,
        "missing_value_issues": 0,
        "invalid_value_issues": 0,
        "total_mismatch_issues": 0,
    }


def test_build_quality_report_counts_equipment():
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

    report = build_quality_report(
        results
    )

    assert report["dataset"][
        "total_records"
    ] == 4

    assert report["equipment"] == {
        "classic": 2,
        "equipped": 1,
        "unknown": 1,
    }


def test_build_quality_report_counts_integrity():
    result = make_result()

    result.total = None

    report = build_quality_report(
        [result]
    )

    assert report["dataset"][
        "total_records"
    ] == 1

    assert report["integrity"][
        "records_with_issues"
    ] == 1

    assert report["integrity"][
        "total_issues"
    ] == 1

    assert report["integrity"][
        "missing_value_issues"
    ] == 1

    assert report["integrity"][
        "invalid_value_issues"
    ] == 0

    assert report["integrity"][
        "total_mismatch_issues"
    ] == 0


def test_build_quality_report_detects_total_mismatch():
    result = make_result(
        total=500.0
    )

    report = build_quality_report(
        [result]
    )

    assert report["integrity"][
        "records_with_issues"
    ] == 1

    assert report["integrity"][
        "total_issues"
    ] == 1

    assert report["integrity"][
        "total_mismatch_issues"
    ] == 1


def test_write_quality_report(tmp_path):
    results = [
        make_result(
            athlete_id="ATH-1",
            equipment=Equipment.CLASSIC,
        ),
        make_result(
            athlete_id="ATH-2",
            equipment=Equipment.EQUIPPED,
        ),
    ]

    output_path = (
        tmp_path
        / "quality_report.json"
    )

    returned_path = write_quality_report(
        results,
        output_path,
    )

    assert returned_path == output_path
    assert output_path.exists()

    data = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    assert data["dataset"][
        "total_records"
    ] == 2

    assert data["equipment"] == {
        "classic": 1,
        "equipped": 1,
        "unknown": 0,
    }


def test_quality_report_is_valid_json(tmp_path):
    output_path = (
        tmp_path
        / "nested"
        / "quality_report.json"
    )

    write_quality_report(
        [make_result()],
        output_path,
    )

    text = output_path.read_text(
        encoding="utf-8"
    )

    parsed = json.loads(text)

    assert isinstance(
        parsed,
        dict,
    )