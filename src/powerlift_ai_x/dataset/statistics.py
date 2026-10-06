from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from powerlift_ai_x.models.competition_result import (
    CompetitionResult,
)


@dataclass(frozen=True)
class NumericStatistics:
    """Basic statistics for one numeric field."""

    count: int
    minimum: float | None
    maximum: float | None
    average: float | None


@dataclass(frozen=True)
class DatasetStatistics:
    """Statistical summary of the canonical dataset."""

    total_records: int

    records_by_year: dict[int, int]
    records_by_competition: dict[str, int]
    records_by_division: dict[str, int]
    records_by_weight_class: dict[str, int]
    records_by_equipment: dict[str, int]
    athletes_by_record_count: dict[int, int]

    bodyweight: NumericStatistics
    best_squat: NumericStatistics
    best_bench: NumericStatistics
    best_deadlift: NumericStatistics
    total: NumericStatistics


def _numeric_statistics(
    values: Iterable[float | None],
) -> NumericStatistics:
    """
    Calculate count, minimum, maximum and average.

    None values are excluded.
    """

    numeric_values = [
        float(value)
        for value in values
        if value is not None
    ]

    if not numeric_values:
        return NumericStatistics(
            count=0,
            minimum=None,
            maximum=None,
            average=None,
        )

    return NumericStatistics(
        count=len(numeric_values),
        minimum=min(numeric_values),
        maximum=max(numeric_values),
        average=sum(numeric_values)
        / len(numeric_values),
    )


def calculate_dataset_statistics(
    results: Iterable[CompetitionResult],
) -> DatasetStatistics:
    """
    Calculate descriptive statistics for canonical results.

    This function does not modify the dataset.
    """

    rows = list(results)

    records_by_year = Counter(
        row.year
        for row in rows
    )

    records_by_competition = Counter(
        row.competition
        for row in rows
    )

    records_by_division = Counter(
        row.division
        for row in rows
    )

    records_by_weight_class = Counter(
        row.weight_class
        for row in rows
    )

    records_by_equipment = Counter(
        row.equipment.value
        for row in rows
    )

    athlete_record_counts = Counter(
        row.athlete_id
        for row in rows
    )

    athletes_by_record_count = Counter(
        athlete_record_counts.values()
    )

    return DatasetStatistics(
        total_records=len(rows),

        records_by_year=dict(
            sorted(
                records_by_year.items()
            )
        ),

        records_by_competition=dict(
            sorted(
                records_by_competition.items()
            )
        ),

        records_by_division=dict(
            sorted(
                records_by_division.items()
            )
        ),

        records_by_weight_class=dict(
            sorted(
                records_by_weight_class.items()
            )
        ),

        records_by_equipment=dict(
            sorted(
                records_by_equipment.items()
            )
        ),

        athletes_by_record_count=dict(
            sorted(
                athletes_by_record_count.items()
            )
        ),

        bodyweight=_numeric_statistics(
            row.bodyweight
            for row in rows
        ),

        best_squat=_numeric_statistics(
            row.best_squat
            for row in rows
        ),

        best_bench=_numeric_statistics(
            row.best_bench
            for row in rows
        ),

        best_deadlift=_numeric_statistics(
            row.best_deadlift
            for row in rows
        ),

        total=_numeric_statistics(
            row.total
            for row in rows
        ),
    )