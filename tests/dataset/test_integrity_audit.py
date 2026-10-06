from powerlift_ai_x.dataset.integrity_audit import (
    IntegrityAuditReport,
    IntegrityIssue,
    audit_integrity,
)
from powerlift_ai_x.models.competition_result import (
    CompetitionResult,
)
from powerlift_ai_x.models.enums import Equipment


def make_result(
    athlete_id="ATH-1",
    total=600.0,
    bodyweight=65.0,
    squat=220.0,
    bench=135.0,
    deadlift=245.0,
):
    return CompetitionResult(
        athlete_id=athlete_id,
        competition="Competition A",
        year=2026,
        division="Open",
        weight_class="66",
        equipment=Equipment.CLASSIC,

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
    report = audit_integrity([])

    assert isinstance(
        report,
        IntegrityAuditReport,
    )

    assert report.total_records == 0
    assert report.records_with_issues == 0
    assert report.total_issues == 0
    assert report.missing_value_issues == 0
    assert report.invalid_value_issues == 0
    assert report.total_mismatch_issues == 0
    assert report.issues == ()


def test_valid_record_has_no_issues():
    result = make_result()

    report = audit_integrity(
        [result]
    )

    assert report.total_records == 1
    assert report.records_with_issues == 0
    assert report.total_issues == 0
    assert report.issues == ()


def test_missing_values_are_detected():
    result = make_result()

    result.bodyweight = None
    result.best_squat = None
    result.best_bench = None
    result.best_deadlift = None
    result.total = None

    report = audit_integrity(
        [result]
    )

    assert report.total_records == 1
    assert report.records_with_issues == 1
    assert report.missing_value_issues == 5
    assert report.invalid_value_issues == 0
    assert report.total_mismatch_issues == 0
    assert report.total_issues == 5

    fields = {
        issue.field
        for issue in report.issues
    }

    assert fields == {
        "bodyweight",
        "best_squat",
        "best_bench",
        "best_deadlift",
        "total",
    }


def test_negative_values_are_detected():
    result = make_result()

    result.bodyweight = -65.0

    report = audit_integrity(
        [result]
    )

    assert report.records_with_issues == 1
    assert report.invalid_value_issues == 1
    assert report.total_issues == 1

    issue = report.issues[0]

    assert isinstance(
        issue,
        IntegrityIssue,
    )

    assert issue.field == "bodyweight"
    assert issue.issue_type == "INVALID_VALUE"
    assert issue.value == -65.0


def test_total_mismatch_is_detected():
    result = make_result(
        total=599.0
    )

    report = audit_integrity(
        [result]
    )

    assert report.records_with_issues == 1
    assert report.total_issues == 1
    assert report.total_mismatch_issues == 1

    issue = report.issues[0]

    assert issue.field == "total"
    assert issue.issue_type == "TOTAL_MISMATCH"
    assert issue.value == 599.0


def test_missing_lift_does_not_create_total_mismatch():
    result = make_result()

    result.best_deadlift = None

    report = audit_integrity(
        [result]
    )

    assert report.missing_value_issues == 1
    assert report.total_mismatch_issues == 0


def test_failed_attempts_are_not_automatically_invalid():
    result = make_result()

    result.squat_3 = None
    result.bench_3 = None
    result.deadlift_3 = None

    report = audit_integrity(
        [result]
    )

    assert report.total_issues == 0


def test_multiple_records_are_counted_correctly():
    valid = make_result(
        athlete_id="ATH-1"
    )

    missing = make_result(
        athlete_id="ATH-2"
    )
    missing.total = None

    mismatch = make_result(
        athlete_id="ATH-3",
        total=500.0,
    )

    report = audit_integrity(
        [
            valid,
            missing,
            mismatch,
        ]
    )

    assert report.total_records == 3
    assert report.records_with_issues == 2
    assert report.total_issues == 2
    assert report.missing_value_issues == 1
    assert report.total_mismatch_issues == 1


def test_audit_does_not_modify_results():
    result = make_result()

    original_total = result.total
    original_squat = result.best_squat

    audit_integrity(
        [result]
    )

    assert result.total == original_total
    assert result.best_squat == original_squat