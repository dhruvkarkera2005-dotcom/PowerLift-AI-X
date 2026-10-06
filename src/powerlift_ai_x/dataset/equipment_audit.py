from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from powerlift_ai_x.models.competition_result import CompetitionResult
from powerlift_ai_x.models.enums import Equipment


@dataclass(frozen=True)
class EquipmentAuditRow:
    """Equipment distribution for one competition."""

    competition: str
    year: int
    classic: int
    equipped: int
    unknown: int

    @property
    def total(self) -> int:
        return (
            self.classic
            + self.equipped
            + self.unknown
        )


@dataclass(frozen=True)
class EquipmentAuditReport:
    """Dataset-wide equipment audit."""

    total_records: int
    classic_records: int
    equipped_records: int
    unknown_records: int

    competitions_with_unknown: int

    rows: tuple[EquipmentAuditRow, ...]


def audit_equipment(
    results: Iterable[CompetitionResult],
) -> EquipmentAuditReport:
    """
    Audit equipment labels without changing any records.

    Results are grouped by competition and year so that
    UNKNOWN equipment can be investigated at source level.
    """

    rows = list(results)

    grouped: dict[
        tuple[str, int],
        Counter[str],
    ] = {}

    for result in rows:
        key = (
            result.competition,
            result.year,
        )

        if key not in grouped:
            grouped[key] = Counter()

        grouped[key][
            result.equipment.value
        ] += 1

    audit_rows: list[EquipmentAuditRow] = []

    for (
        competition,
        year,
    ), counts in sorted(
        grouped.items(),
        key=lambda item: (
            item[0][1],
            item[0][0],
        ),
    ):
        audit_rows.append(
            EquipmentAuditRow(
                competition=competition,
                year=year,
                classic=counts.get(
                    Equipment.CLASSIC.value,
                    0,
                ),
                equipped=counts.get(
                    Equipment.EQUIPPED.value,
                    0,
                ),
                unknown=counts.get(
                    Equipment.UNKNOWN.value,
                    0,
                ),
            )
        )

    classic_records = sum(
        row.classic
        for row in audit_rows
    )

    equipped_records = sum(
        row.equipped
        for row in audit_rows
    )

    unknown_records = sum(
        row.unknown
        for row in audit_rows
    )

    competitions_with_unknown = sum(
        1
        for row in audit_rows
        if row.unknown > 0
    )

    return EquipmentAuditReport(
        total_records=len(rows),
        classic_records=classic_records,
        equipped_records=equipped_records,
        unknown_records=unknown_records,
        competitions_with_unknown=(
            competitions_with_unknown
        ),
        rows=tuple(audit_rows),
    )


def unknown_equipment_rows(
    results: Iterable[CompetitionResult],
) -> list[CompetitionResult]:
    """
    Return only records whose equipment is UNKNOWN.

    This is an inspection helper and does not modify
    the supplied records.
    """

    return [
        result
        for result in results
        if result.equipment == Equipment.UNKNOWN
    ]