from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from powerlift_ai_x.parsing.unified_parser import (
    ParsedSource,
    parse_directory,
)


@dataclass
class ValidationIssue:
    source_file: str
    issue_type: str
    athlete_name: str
    message: str
    fields: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    total_sources: int = 0
    successful_sources: int = 0
    failed_sources: int = 0

    total_rows: int = 0
    parsed_rows: int = 0
    incomplete_rows: int = 0
    review_rows: int = 0

    total_mismatches: int = 0

    missing_weight_class: int = 0
    missing_division: int = 0

    invalid_bodyweight: int = 0
    invalid_best_lifts: int = 0
    invalid_total: int = 0

    duplicate_rows: int = 0

    issues: list[ValidationIssue] = field(
        default_factory=list
    )


def _valid_non_negative(
    value: object,
) -> bool:
    if value is None:
        return True

    return (
        isinstance(value, (int, float))
        and value >= 0
    )


def validate_row(
    source_file: str,
    result: dict[str, object],
    report: ValidationReport,
) -> None:
    row = result.get("row")

    if row is None:
        report.review_rows += 1

        report.issues.append(
            ValidationIssue(
                source_file=source_file,
                issue_type="MISSING_ROW",
                athlete_name="",
                message="Result has no ParsedRow.",
            )
        )

        return

    report.total_rows += 1

    athlete_name = getattr(
        row,
        "athlete_name",
        "",
    )

    status = result.get(
        "status",
        getattr(row, "status", None),
    )

    if status == "PARSED":
        report.parsed_rows += 1

    elif status == "INCOMPLETE":
        report.incomplete_rows += 1

    elif status == "REVIEW":
        report.review_rows += 1

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    if result.get("weight_class") is None:
        report.missing_weight_class += 1

        report.issues.append(
            ValidationIssue(
                source_file,
                "MISSING_WEIGHT_CLASS",
                athlete_name,
                "Weight class is missing.",
                ["weight_class"],
            )
        )

    if result.get("division") is None:
        report.missing_division += 1

        report.issues.append(
            ValidationIssue(
                source_file,
                "MISSING_DIVISION",
                athlete_name,
                "Division is missing.",
                ["division"],
            )
        )

    # --------------------------------------------------------
    # Bodyweight
    # --------------------------------------------------------

    bodyweight = getattr(
        row,
        "bodyweight",
        None,
    )

    if not _valid_non_negative(
        bodyweight
    ):
        report.invalid_bodyweight += 1

        report.issues.append(
            ValidationIssue(
                source_file,
                "INVALID_BODYWEIGHT",
                athlete_name,
                f"Invalid bodyweight: {bodyweight}",
                ["bodyweight"],
            )
        )

    # --------------------------------------------------------
    # Source-provided best lifts
    #
    # IMPORTANT:
    #
    # We do NOT compare best_lift with max(attempts).
    #
    # The source PDFs have format-specific attempt semantics.
    # Therefore the parser's explicit best value is preserved
    # as authoritative.
    # --------------------------------------------------------

    best_values = {
        "best_squat": getattr(
            row,
            "best_squat",
            None,
        ),
        "best_bench": getattr(
            row,
            "best_bench",
            None,
        ),
        "best_deadlift": getattr(
            row,
            "best_deadlift",
            None,
        ),
    }

    for field_name, value in best_values.items():

        if not _valid_non_negative(value):
            report.invalid_best_lifts += 1

            report.issues.append(
                ValidationIssue(
                    source_file,
                    "INVALID_BEST_LIFT",
                    athlete_name,
                    f"Invalid {field_name}: {value}",
                    [field_name],
                )
            )

    # --------------------------------------------------------
    # Total consistency
    #
    # This remains a strong check because the source total
    # should equal the three source-provided best lifts when
    # all three exist.
    # --------------------------------------------------------

    total = getattr(
        row,
        "total",
        None,
    )

    best_squat = best_values[
        "best_squat"
    ]

    best_bench = best_values[
        "best_bench"
    ]

    best_deadlift = best_values[
        "best_deadlift"
    ]

    if (
        total is not None
        and best_squat is not None
        and best_bench is not None
        and best_deadlift is not None
    ):
        expected_total = (
            best_squat
            + best_bench
            + best_deadlift
        )

        if total != expected_total:
            report.total_mismatches += 1

            report.issues.append(
                ValidationIssue(
                    source_file,
                    "TOTAL_MISMATCH",
                    athlete_name,
                    (
                        f"Total={total}, "
                        f"expected={expected_total}"
                    ),
                    [
                        "total",
                        "best_squat",
                        "best_bench",
                        "best_deadlift",
                    ],
                )
            )

    if not _valid_non_negative(total):
        report.invalid_total += 1

        report.issues.append(
            ValidationIssue(
                source_file,
                "INVALID_TOTAL",
                athlete_name,
                f"Invalid total: {total}",
                ["total"],
            )
        )


def _duplicate_key(
    source_file: str,
    result: dict[str, object],
) -> tuple | None:
    row = result.get("row")

    if row is None:
        return None

    name = getattr(
        row,
        "athlete_name",
        "",
    )

    return (
        source_file,
        name.strip().upper(),
        result.get("weight_class"),
        result.get("division"),
        getattr(
            row,
            "bodyweight",
            None,
        ),
        getattr(
            row,
            "total",
            None,
        ),
    )


def validate_sources(
    sources: list[ParsedSource],
) -> ValidationReport:
    report = ValidationReport()

    report.total_sources = len(
        sources
    )

    seen: set[tuple] = set()

    for source in sources:

        if source.status == "SUCCESS":
            report.successful_sources += 1
        else:
            report.failed_sources += 1

            report.issues.append(
                ValidationIssue(
                    source_file=source.source_file,
                    issue_type="SOURCE_ERROR",
                    athlete_name="",
                    message=(
                        source.error
                        or "Source parsing failed."
                    ),
                )
            )

        for result in source.results:

            key = _duplicate_key(
                source.source_file,
                result,
            )

            if key is not None:

                if key in seen:
                    report.duplicate_rows += 1

                    row = result.get(
                        "row"
                    )

                    report.issues.append(
                        ValidationIssue(
                            source_file=source.source_file,
                            issue_type="DUPLICATE_ROW",
                            athlete_name=(
                                getattr(
                                    row,
                                    "athlete_name",
                                    "",
                                )
                                if row is not None
                                else ""
                            ),
                            message=(
                                "Potential duplicate "
                                "result row."
                            ),
                        )
                    )

                else:
                    seen.add(key)

            validate_row(
                source_file=source.source_file,
                result=result,
                report=report,
            )

    return report


def validate_directory(
    directory: str | Path,
) -> ValidationReport:
    sources = parse_directory(
        directory
    )

    return validate_sources(
        sources
    )


def print_report(
    report: ValidationReport,
) -> None:
    print(
        "=========================================="
    )
    print(
        "POWERLIFT DATASET VALIDATION"
    )
    print(
        "=========================================="
    )

    print(
        f"SOURCES:              "
        f"{report.total_sources}"
    )

    print(
        f"SUCCESSFUL SOURCES:   "
        f"{report.successful_sources}"
    )

    print(
        f"FAILED SOURCES:       "
        f"{report.failed_sources}"
    )

    print()

    print(
        f"TOTAL ROWS:           "
        f"{report.total_rows}"
    )

    print(
        f"PARSED:               "
        f"{report.parsed_rows}"
    )

    print(
        f"INCOMPLETE:           "
        f"{report.incomplete_rows}"
    )

    print(
        f"REVIEW:               "
        f"{report.review_rows}"
    )

    print()

    print(
        f"TOTAL MISMATCHES:     "
        f"{report.total_mismatches}"
    )

    print(
        f"MISSING WEIGHT CLASS: "
        f"{report.missing_weight_class}"
    )

    print(
        f"MISSING DIVISION:     "
        f"{report.missing_division}"
    )

    print(
        f"DUPLICATE ROWS:       "
        f"{report.duplicate_rows}"
    )

    print(
        f"INVALID BODYWEIGHT:   "
        f"{report.invalid_bodyweight}"
    )

    print(
        f"INVALID BEST LIFTS:   "
        f"{report.invalid_best_lifts}"
    )

    print(
        f"INVALID TOTAL:        "
        f"{report.invalid_total}"
    )

    print()

    print(
        f"TOTAL ISSUES:         "
        f"{len(report.issues)}"
    )

    print(
        "=========================================="
    )