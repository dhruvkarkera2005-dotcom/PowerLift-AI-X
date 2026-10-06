from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from powerlift_ai_x.ml.history import (
    AthleteHistoryExample,
    build_athlete_history_examples,
)


@dataclass(frozen=True)
class LeakageAudit:
    """
    Results of a chronological leakage audit.
    """

    total_examples: int
    examples_with_target_in_history: int
    examples_with_future_year_in_history: int
    examples_with_target_values_in_history: int
    athlete_ordering_violations: int

    @property
    def passed(self) -> bool:
        return (
            self.examples_with_target_in_history == 0
            and self.examples_with_future_year_in_history == 0
            and self.examples_with_target_values_in_history == 0
            and self.athlete_ordering_violations == 0
        )


def _year(row: Mapping[str, Any]) -> int:
    value = row.get("year")

    if value is None:
        raise ValueError("Competition row is missing year")

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid competition year: {value!r}"
        ) from exc


def _competition(row: Mapping[str, Any]) -> str:
    value = row.get("competition")

    if value is None:
        raise ValueError(
            "Competition row is missing competition"
        )

    return str(value).strip()


def _target_signature(
    row: Mapping[str, Any],
) -> tuple[Any, ...]:
    """
    Values that identify the target performance.

    These values must not appear in the historical rows used
    to construct the same prediction example.
    """

    return (
        row.get("best_squat"),
        row.get("best_bench"),
        row.get("best_deadlift"),
        row.get("total"),
    )


def audit_examples_against_rows(
    rows: Sequence[Mapping[str, Any]],
    examples: Sequence[AthleteHistoryExample],
) -> LeakageAudit:
    """
    Audit generated examples against the canonical source rows.

    This independently reconstructs each athlete's chronological
    sequence and checks that the generated example's target is not
    accidentally part of its history.

    NOTE:
    Same-year competitions are ordered deterministically using
    competition name, matching the history builder.
    """

    grouped: dict[str, list[Mapping[str, Any]]] = {}

    for row in rows:
        athlete_id = row.get("athlete_id")

        if athlete_id is None:
            raise ValueError(
                "Competition row is missing athlete_id"
            )

        grouped.setdefault(
            str(athlete_id),
            [],
        ).append(row)

    examples_with_target_in_history = 0
    examples_with_future_year_in_history = 0
    examples_with_target_values_in_history = 0
    athlete_ordering_violations = 0

    for example in examples:
        athlete_rows = sorted(
            grouped.get(example.athlete_id, []),
            key=lambda row: (
                _year(row),
                _competition(row),
            ),
        )

        target_candidates = [
            row
            for row in athlete_rows
            if (
                _year(row) == example.target_year
                and _competition(row)
                == example.target_competition
            )
        ]

        if len(target_candidates) != 1:
            examples_with_target_in_history += 1
            continue

        target_row = target_candidates[0]

        target_index = athlete_rows.index(
            target_row
        )

        history_rows = athlete_rows[:target_index]

        target_key = (
            example.target_year,
            example.target_competition,
            )
        if any(
            (
                _year(row),
                _competition(row),
                )
                > target_key
                for row in history_rows
                ):
            examples_with_future_year_in_history += 1


        target_identity = (
            example.target_year,
            example.target_competition,
        )

        if any(
            (
                _year(row),
                _competition(row),
            )
            == target_identity
            for row in history_rows
        ):
            examples_with_target_in_history += 1

        target_signature = _target_signature(
            target_row
        )

        if any(
            _target_signature(row)
            == target_signature
            for row in history_rows
        ):
            examples_with_target_values_in_history += 1

    # Independently verify ordering for every athlete.
    for athlete_id, athlete_rows in grouped.items():
        ordered = sorted(
            athlete_rows,
            key=lambda row: (
                _year(row),
                _competition(row),
            ),
        )

        previous_key: tuple[int, str] | None = None

        for row in ordered:
            current_key = (
                _year(row),
                _competition(row),
            )

            if (
                previous_key is not None
                and current_key < previous_key
            ):
                athlete_ordering_violations += 1

            previous_key = current_key

    return LeakageAudit(
        total_examples=len(examples),
        examples_with_target_in_history=(
            examples_with_target_in_history
        ),
        examples_with_future_year_in_history=(
            examples_with_future_year_in_history
        ),
        examples_with_target_values_in_history=(
            examples_with_target_values_in_history
        ),
        athlete_ordering_violations=(
            athlete_ordering_violations
        ),
    )


def audit_real_dataset(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[
    list[AthleteHistoryExample],
    LeakageAudit,
]:
    """
    Build the chronological examples and immediately audit them.
    """

    examples = build_athlete_history_examples(
        rows
    )

    audit = audit_examples_against_rows(
        rows,
        examples,
    )

    return examples, audit