from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


TARGET_FIELDS = (
    "best_squat",
    "best_bench",
    "best_deadlift",
    "total",
)


@dataclass(frozen=True)
class NextCompetitionTarget:
    """
    Target values from an athlete's next competition.

    These values must come exclusively from the future
    competition that we are trying to predict.
    """

    best_squat: float | None
    best_bench: float | None
    best_deadlift: float | None
    total: float | None


def extract_next_competition_target(
    row: Mapping[str, Any],
) -> NextCompetitionTarget:
    """
    Extract the target values from one future competition row.

    This function intentionally does not calculate or modify
    the recorded best values. It preserves the canonical
    dataset values exactly.
    """

    return NextCompetitionTarget(
        best_squat=row.get("best_squat"),
        best_bench=row.get("best_bench"),
        best_deadlift=row.get("best_deadlift"),
        total=row.get("total"),
    )


def target_is_complete(
    target: NextCompetitionTarget,
) -> bool:
    """
    Return True when all four prediction targets are present.
    """

    return all(
        getattr(target, field) is not None
        for field in TARGET_FIELDS
    )


def target_to_dict(
    target: NextCompetitionTarget,
) -> dict[str, Any]:
    """
    Convert a target object into a plain dictionary.
    """

    return {
        field: getattr(target, field)
        for field in TARGET_FIELDS
    }