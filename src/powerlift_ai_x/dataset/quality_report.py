from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from powerlift_ai_x.dataset.equipment_audit import (
    audit_equipment,
)
from powerlift_ai_x.dataset.integrity_audit import (
    audit_integrity,
)
from powerlift_ai_x.models.competition_result import (
    CompetitionResult,
)


def build_quality_report(
    results: Iterable[CompetitionResult],
) -> dict[str, object]:
    """
    Build a complete data-quality report.

    The report combines:
    - dataset size
    - equipment distribution
    - integrity findings
    - missing-value counts
    - duplicate information supplied by the caller

    This function does not modify the dataset.
    """

    rows = list(results)

    equipment = audit_equipment(rows)
    integrity = audit_integrity(rows)

    return {
        "dataset": {
            "total_records": len(rows),
        },
        "equipment": {
            "classic": equipment.classic_records,
            "equipped": equipment.equipped_records,
            "unknown": equipment.unknown_records,
        },
        "integrity": {
            "records_with_issues": (
                integrity.records_with_issues
            ),
            "total_issues": (
                integrity.total_issues
            ),
            "missing_value_issues": (
                integrity.missing_value_issues
            ),
            "invalid_value_issues": (
                integrity.invalid_value_issues
            ),
            "total_mismatch_issues": (
                integrity.total_mismatch_issues
            ),
        },
    }


def write_quality_report(
    results: Iterable[CompetitionResult],
    output_path: str | Path,
) -> Path:
    """
    Build and write the quality report as JSON.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = build_quality_report(results)

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return output_path