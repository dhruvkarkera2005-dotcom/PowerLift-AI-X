from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from powerlift_ai_x.models.competition_result import CompetitionResult


@dataclass(frozen=True)
class DuplicateGroup:
    """A group of canonical results with the same identity key."""

    key: tuple[object, ...]
    records: tuple[CompetitionResult, ...]


@dataclass(frozen=True)
class DeduplicationReport:
    """Summary of duplicate detection."""

    total_records: int
    unique_records: int
    duplicate_records: int
    duplicate_groups: int


def make_result_key(
    result: CompetitionResult,
) -> tuple[object, ...]:
    """
    Build a stable identity key for one competition result.

    Athlete identity alone is deliberately insufficient because
    an athlete can legitimately compete multiple times.
    """

    return (
        result.athlete_id,
        result.competition,
        result.year,
        result.division,
        result.weight_class,
        result.equipment.value,
        result.bodyweight,
        result.squat_1,
        result.squat_2,
        result.squat_3,
        result.best_squat,
        result.bench_1,
        result.bench_2,
        result.bench_3,
        result.best_bench,
        result.deadlift_1,
        result.deadlift_2,
        result.deadlift_3,
        result.best_deadlift,
        result.total,
        result.place,
    )


def find_duplicate_groups(
    results: Iterable[CompetitionResult],
) -> list[DuplicateGroup]:
    """
    Find exact duplicate canonical records.

    Records are grouped by the complete canonical result key.
    Legitimate repeated performances at different competitions
    or years are therefore not considered duplicates.
    """

    groups: dict[
        tuple[object, ...],
        list[CompetitionResult],
    ] = {}

    for result in results:
        key = make_result_key(result)

        groups.setdefault(
            key,
            [],
        ).append(result)

    return [
        DuplicateGroup(
            key=key,
            records=tuple(records),
        )
        for key, records in groups.items()
        if len(records) > 1
    ]


def build_deduplication_report(
    results: Iterable[CompetitionResult],
) -> DeduplicationReport:
    """
    Build duplicate statistics without modifying the dataset.
    """

    rows = list(results)

    duplicate_groups = find_duplicate_groups(rows)

    duplicate_records = sum(
        len(group.records) - 1
        for group in duplicate_groups
    )

    return DeduplicationReport(
        total_records=len(rows),
        unique_records=len(rows) - duplicate_records,
        duplicate_records=duplicate_records,
        duplicate_groups=len(duplicate_groups),
    )


def deduplicate_results(
    results: Iterable[CompetitionResult],
) -> list[CompetitionResult]:
    """
    Return canonical results with exact duplicates removed.

    The first occurrence is retained.

    This function does NOT merge similar records and does NOT
    remove an athlete merely because the athlete appears more
    than once.
    """

    seen: set[tuple[object, ...]] = set()
    unique: list[CompetitionResult] = []

    for result in results:
        key = make_result_key(result)

        if key in seen:
            continue

        seen.add(key)
        unique.append(result)

    return unique