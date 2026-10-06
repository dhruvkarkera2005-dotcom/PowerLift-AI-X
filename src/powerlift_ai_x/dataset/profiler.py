from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from powerlift_ai_x.models.competition_result import (
    CompetitionResult,
)


@dataclass
class DatasetProfile:
    """Summary statistics for the canonical dataset."""

    total_records: int

    unique_athletes: int
    competitions: int
    years: int
    divisions: int
    weight_classes: int

    equipment: dict[str, int]

    squat_missing: int
    squat_valid: int
    squat_failed_attempts: int

    bench_missing: int
    bench_valid: int
    bench_failed_attempts: int

    deadlift_missing: int
    deadlift_valid: int
    deadlift_failed_attempts: int

    total_missing: int
    total_valid: int


def _count_failed_attempts(
    attempts: Iterable[float | None],
) -> int:
    """
    Count failed attempts.

    Failed attempts are represented by negative values
    in the canonical dataset.
    """

    return sum(
        1
        for attempt in attempts
        if attempt is not None and attempt < 0
    )


def profile_dataset(
    results: Iterable[CompetitionResult],
) -> DatasetProfile:
    """
    Build a profile of the canonical CompetitionResult dataset.
    """

    rows = list(results)

    athlete_ids = {
        row.athlete_id
        for row in rows
    }

    competitions = {
        row.competition
        for row in rows
    }

    years = {
        row.year
        for row in rows
    }

    divisions = {
        row.division
        for row in rows
    }

    weight_classes = {
        row.weight_class
        for row in rows
    }

    equipment_counter = Counter(
        row.equipment.value
        for row in rows
    )

    squat_missing = 0
    squat_valid = 0
    squat_failed_attempts = 0

    bench_missing = 0
    bench_valid = 0
    bench_failed_attempts = 0

    deadlift_missing = 0
    deadlift_valid = 0
    deadlift_failed_attempts = 0

    total_missing = 0
    total_valid = 0

    for row in rows:

        # ----------------------------------------------------
        # Squat
        # ----------------------------------------------------

        squat_attempts = (
            row.squat_1,
            row.squat_2,
            row.squat_3,
        )

        squat_failed_attempts += (
            _count_failed_attempts(
                squat_attempts
            )
        )

        if row.best_squat is None:
            squat_missing += 1
        else:
            squat_valid += 1

        # ----------------------------------------------------
        # Bench
        # ----------------------------------------------------

        bench_attempts = (
            row.bench_1,
            row.bench_2,
            row.bench_3,
        )

        bench_failed_attempts += (
            _count_failed_attempts(
                bench_attempts
            )
        )

        if row.best_bench is None:
            bench_missing += 1
        else:
            bench_valid += 1

        # ----------------------------------------------------
        # Deadlift
        # ----------------------------------------------------

        deadlift_attempts = (
            row.deadlift_1,
            row.deadlift_2,
            row.deadlift_3,
        )

        deadlift_failed_attempts += (
            _count_failed_attempts(
                deadlift_attempts
            )
        )

        if row.best_deadlift is None:
            deadlift_missing += 1
        else:
            deadlift_valid += 1

        # ----------------------------------------------------
        # Total
        # ----------------------------------------------------

        if row.total is None:
            total_missing += 1
        else:
            total_valid += 1

    return DatasetProfile(
        total_records=len(rows),

        unique_athletes=len(athlete_ids),
        competitions=len(competitions),
        years=len(years),
        divisions=len(divisions),
        weight_classes=len(weight_classes),

        equipment=dict(
            sorted(
                equipment_counter.items()
            )
        ),

        squat_missing=squat_missing,
        squat_valid=squat_valid,
        squat_failed_attempts=squat_failed_attempts,

        bench_missing=bench_missing,
        bench_valid=bench_valid,
        bench_failed_attempts=bench_failed_attempts,

        deadlift_missing=deadlift_missing,
        deadlift_valid=deadlift_valid,
        deadlift_failed_attempts=deadlift_failed_attempts,

        total_missing=total_missing,
        total_valid=total_valid,
    )