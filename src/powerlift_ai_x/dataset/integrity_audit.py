from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from powerlift_ai_x.models.competition_result import CompetitionResult


@dataclass(frozen=True)
class IntegrityIssue:
    """One detected data-integrity issue."""

    athlete_id: str
    competition: str
    year: int
    field: str
    issue_type: str
    value: object
    message: str


@dataclass(frozen=True)
class IntegrityAuditReport:
    """Dataset-wide integrity audit."""

    total_records: int
    records_with_issues: int
    total_issues: int
    missing_value_issues: int
    invalid_value_issues: int
    total_mismatch_issues: int
    issues: tuple[IntegrityIssue, ...]


def _is_missing(value: object) -> bool:
    return value is None


def _is_negative(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and value < 0
    )


def audit_integrity(
    results: Iterable[CompetitionResult],
) -> IntegrityAuditReport:
    """
    Audit canonical records for basic value-quality problems.

    This function does not modify any records.

    Checks:
    - missing bodyweight
    - missing best lifts
    - missing total
    - negative numeric values
    - total inconsistent with best squat + bench + deadlift

    Failed attempts represented by None are treated as
    missing values and are not automatically considered errors.
    """

    rows = list(results)

    issues: list[IntegrityIssue] = []

    for row in rows:
        def add_issue(
            field: str,
            issue_type: str,
            value: object,
            message: str,
        ) -> None:
            issues.append(
                IntegrityIssue(
                    athlete_id=row.athlete_id,
                    competition=row.competition,
                    year=row.year,
                    field=field,
                    issue_type=issue_type,
                    value=value,
                    message=message,
                )
            )

        # --------------------------------------------------
        # Required canonical values
        # --------------------------------------------------

        required_fields = (
            "bodyweight",
            "best_squat",
            "best_bench",
            "best_deadlift",
            "total",
        )

        for field in required_fields:
            value = getattr(row, field)

            if _is_missing(value):
                add_issue(
                    field=field,
                    issue_type="MISSING_VALUE",
                    value=value,
                    message=(
                        f"{field} is missing"
                    ),
                )

        # --------------------------------------------------
        # Negative values
        # --------------------------------------------------

        numeric_fields = (
            "bodyweight",
            "squat_1",
            "squat_2",
            "squat_3",
            "best_squat",
            "bench_1",
            "bench_2",
            "bench_3",
            "best_bench",
            "deadlift_1",
            "deadlift_2",
            "deadlift_3",
            "best_deadlift",
            "total",
        )

        for field in numeric_fields:
            value = getattr(row, field)

            if _is_negative(value):
                add_issue(
                    field=field,
                    issue_type="INVALID_VALUE",
                    value=value,
                    message=(
                        f"{field} cannot be negative"
                    ),
                )

        # --------------------------------------------------
        # Total consistency
        # --------------------------------------------------

        if (
            row.best_squat is not None
            and row.best_bench is not None
            and row.best_deadlift is not None
            and row.total is not None
        ):
            expected_total = (
                row.best_squat
                + row.best_bench
                + row.best_deadlift
            )

            if row.total != expected_total:
                add_issue(
                    field="total",
                    issue_type="TOTAL_MISMATCH",
                    value=row.total,
                    message=(
                        "Total does not equal "
                        "best squat + best bench + "
                        "best deadlift"
                    ),
                )

    records_with_issues = len(
        {
            (
                issue.athlete_id,
                issue.competition,
                issue.year,
            )
            for issue in issues
        }
    )

    missing_value_issues = sum(
        issue.issue_type == "MISSING_VALUE"
        for issue in issues
    )

    invalid_value_issues = sum(
        issue.issue_type == "INVALID_VALUE"
        for issue in issues
    )

    total_mismatch_issues = sum(
        issue.issue_type == "TOTAL_MISMATCH"
        for issue in issues
    )

    return IntegrityAuditReport(
        total_records=len(rows),
        records_with_issues=records_with_issues,
        total_issues=len(issues),
        missing_value_issues=missing_value_issues,
        invalid_value_issues=invalid_value_issues,
        total_mismatch_issues=total_mismatch_issues,
        issues=tuple(issues),
    )