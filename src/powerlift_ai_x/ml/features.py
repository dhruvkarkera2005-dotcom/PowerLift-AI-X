from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


ATTEMPT_FIELDS = (
    "squat_1",
    "squat_2",
    "squat_3",
    "bench_1",
    "bench_2",
    "bench_3",
    "deadlift_1",
    "deadlift_2",
    "deadlift_3",
)

BEST_FIELDS = (
    "best_squat",
    "best_bench",
    "best_deadlift",
)

HISTORICAL_FIELDS = (
    *ATTEMPT_FIELDS,
    *BEST_FIELDS,
    "total",
    "bodyweight",
)


@dataclass(frozen=True)
class PreviousCompetition:
    """
    Complete performance information from one previous
    competition.

    The values are copied from the canonical dataset.
    No attempt value is recalculated or replaced.
    """

    squat_1: float | None
    squat_2: float | None
    squat_3: float | None
    best_squat: float | None

    bench_1: float | None
    bench_2: float | None
    bench_3: float | None
    best_bench: float | None

    deadlift_1: float | None
    deadlift_2: float | None
    deadlift_3: float | None
    best_deadlift: float | None

    total: float | None
    bodyweight: float | None


@dataclass(frozen=True)
class HistoricalFeatures:
    """
    Historical features for predicting an athlete's next
    competition.

    Only competitions that occurred before the target
    competition may be supplied.

    The most recent previous competition is preserved in full,
    including all nine attempts.

    Historical maxima are calculated independently across all
    previous competitions.
    """

    previous_competition_count: int

    previous: PreviousCompetition | None

    historical_best_squat: float | None
    historical_best_bench: float | None
    historical_best_deadlift: float | None
    historical_best_total: float | None

    historical_best_squat_attempt: float | None
    historical_best_bench_attempt: float | None
    historical_best_deadlift_attempt: float | None


def _numeric_value(
    row: Mapping[str, Any],
    field: str,
) -> float | None:
    """
    Return a canonical numeric value.

    None remains None.

    Boolean values are rejected because bool is a subclass
    of int in Python and must not be treated as a lift value.
    """

    value = row.get(field)

    if value is None:
        return None

    if isinstance(value, bool):
        raise TypeError(
            f"{field} cannot be a boolean"
        )

    if isinstance(value, (int, float)):
        return float(value)

    raise TypeError(
        f"{field} must be numeric or None, "
        f"got {type(value).__name__}"
    )


def _make_previous_competition(
    row: Mapping[str, Any],
) -> PreviousCompetition:
    """
    Copy the complete previous competition record relevant
    to performance prediction.
    """

    return PreviousCompetition(
        squat_1=_numeric_value(row, "squat_1"),
        squat_2=_numeric_value(row, "squat_2"),
        squat_3=_numeric_value(row, "squat_3"),
        best_squat=_numeric_value(row, "best_squat"),
        bench_1=_numeric_value(row, "bench_1"),
        bench_2=_numeric_value(row, "bench_2"),
        bench_3=_numeric_value(row, "bench_3"),
        best_bench=_numeric_value(row, "best_bench"),
        deadlift_1=_numeric_value(row, "deadlift_1"),
        deadlift_2=_numeric_value(row, "deadlift_2"),
        deadlift_3=_numeric_value(row, "deadlift_3"),
        best_deadlift=_numeric_value(
            row,
            "best_deadlift",
        ),
        total=_numeric_value(row, "total"),
        bodyweight=_numeric_value(
            row,
            "bodyweight",
        ),
    )


def _values(
    history: Sequence[Mapping[str, Any]],
    field: str,
) -> list[float]:
    """
    Collect available numeric values for a field.
    """

    result: list[float] = []

    for row in history:
        value = _numeric_value(row, field)

        if value is not None:
            result.append(value)

    return result


def _attempt_values(
    history: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
) -> list[float]:
    """
    Collect numeric attempt values across all previous
    competitions.
    """

    result: list[float] = []

    for row in history:
        for field in fields:
            value = _numeric_value(row, field)

            if value is not None:
                result.append(value)

    return result


def build_historical_features(
    history: Sequence[Mapping[str, Any]],
) -> HistoricalFeatures:
    """
    Build complete historical features.

    IMPORTANT:
    This function does not search for or include a target row.

    The caller must supply only competitions that occurred
    before the target competition.

    History must be ordered chronologically, with the most
    recent previous competition as the final element.
    """

    if not history:
        return HistoricalFeatures(
            previous_competition_count=0,
            previous=None,
            historical_best_squat=None,
            historical_best_bench=None,
            historical_best_deadlift=None,
            historical_best_total=None,
            historical_best_squat_attempt=None,
            historical_best_bench_attempt=None,
            historical_best_deadlift_attempt=None,
        )

    previous = _make_previous_competition(
        history[-1]
    )

    squat_best_values = _values(
        history,
        "best_squat",
    )

    bench_best_values = _values(
        history,
        "best_bench",
    )

    deadlift_best_values = _values(
        history,
        "best_deadlift",
    )

    total_values = _values(
        history,
        "total",
    )

    squat_attempt_values = _attempt_values(
        history,
        (
            "squat_1",
            "squat_2",
            "squat_3",
        ),
    )

    bench_attempt_values = _attempt_values(
        history,
        (
            "bench_1",
            "bench_2",
            "bench_3",
        ),
    )

    deadlift_attempt_values = _attempt_values(
        history,
        (
            "deadlift_1",
            "deadlift_2",
            "deadlift_3",
        ),
    )

    return HistoricalFeatures(
        previous_competition_count=len(history),
        previous=previous,
        historical_best_squat=(
            max(squat_best_values)
            if squat_best_values
            else None
        ),
        historical_best_bench=(
            max(bench_best_values)
            if bench_best_values
            else None
        ),
        historical_best_deadlift=(
            max(deadlift_best_values)
            if deadlift_best_values
            else None
        ),
        historical_best_total=(
            max(total_values)
            if total_values
            else None
        ),
        historical_best_squat_attempt=(
            max(squat_attempt_values)
            if squat_attempt_values
            else None
        ),
        historical_best_bench_attempt=(
            max(bench_attempt_values)
            if bench_attempt_values
            else None
        ),
        historical_best_deadlift_attempt=(
            max(deadlift_attempt_values)
            if deadlift_attempt_values
            else None
        ),
    )


def previous_competition_to_dict(
    previous: PreviousCompetition | None,
) -> dict[str, Any] | None:
    """
    Convert a previous competition to a dictionary.
    """

    if previous is None:
        return None

    return {
        "squat_1": previous.squat_1,
        "squat_2": previous.squat_2,
        "squat_3": previous.squat_3,
        "best_squat": previous.best_squat,
        "bench_1": previous.bench_1,
        "bench_2": previous.bench_2,
        "bench_3": previous.bench_3,
        "best_bench": previous.best_bench,
        "deadlift_1": previous.deadlift_1,
        "deadlift_2": previous.deadlift_2,
        "deadlift_3": previous.deadlift_3,
        "best_deadlift": previous.best_deadlift,
        "total": previous.total,
        "bodyweight": previous.bodyweight,
    }


def features_to_dict(
    features: HistoricalFeatures,
) -> dict[str, Any]:
    """
    Convert historical features into a serializable dictionary.
    """

    return {
        "previous_competition_count": (
            features.previous_competition_count
        ),
        "previous": previous_competition_to_dict(
            features.previous
        ),
        "historical_best_squat": (
            features.historical_best_squat
        ),
        "historical_best_bench": (
            features.historical_best_bench
        ),
        "historical_best_deadlift": (
            features.historical_best_deadlift
        ),
        "historical_best_total": (
            features.historical_best_total
        ),
        "historical_best_squat_attempt": (
            features.historical_best_squat_attempt
        ),
        "historical_best_bench_attempt": (
            features.historical_best_bench_attempt
        ),
        "historical_best_deadlift_attempt": (
            features.historical_best_deadlift_attempt
        ),
    }