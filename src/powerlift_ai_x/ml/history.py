from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from powerlift_ai_x.ml.features import (
    HistoricalFeatures,
    build_historical_features,
    features_to_dict,
)
from powerlift_ai_x.ml.target import (
    NextCompetitionTarget,
    extract_next_competition_target,
    target_to_dict,
)


@dataclass(frozen=True)
class AthleteHistoryExample:
    """
    One supervised-learning example.

    `history` contains only competitions strictly before the
    target competition.

    `target` contains the athlete's next competition result.
    """

    athlete_id: str
    target_year: int
    target_competition: str

    features: HistoricalFeatures
    target: NextCompetitionTarget


def _year(row: Mapping[str, Any]) -> int:
    """
    Return the competition year as an integer.
    """

    value = row.get("year")

    if value is None:
        raise ValueError("Competition row is missing year")

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid competition year: {value!r}"
        ) from exc


def _athlete_id(row: Mapping[str, Any]) -> str:
    """
    Return a non-empty athlete identifier.
    """

    value = row.get("athlete_id")

    if value is None:
        raise ValueError("Competition row is missing athlete_id")

    athlete_id = str(value).strip()

    if not athlete_id:
        raise ValueError("athlete_id cannot be empty")

    return athlete_id


def _competition_name(
    row: Mapping[str, Any],
) -> str:
    """
    Return a competition name.
    """

    value = row.get("competition")

    if value is None:
        raise ValueError(
            "Competition row is missing competition"
        )

    competition = str(value).strip()

    if not competition:
        raise ValueError(
            "competition cannot be empty"
        )

    return competition


def _sort_key(
    row: Mapping[str, Any],
) -> tuple[int, str]:
    """
    Sort primarily by year and secondarily by competition name.

    This provides deterministic ordering when multiple competitions
    for the same athlete occur in the same year.

    A later stage can introduce an explicit competition date when
    the source data provides one.
    """

    return (
        _year(row),
        _competition_name(row),
    )


def build_athlete_history_examples(
    rows: Sequence[Mapping[str, Any]],
) -> list[AthleteHistoryExample]:
    """
    Build chronological next-competition examples.

    For every athlete:

        competition 1 -> no training example
        competition 2 -> history = competition 1
        competition 3 -> history = competitions 1 + 2
        ...

    The target competition is NEVER included in its own history.

    Every athlete's records are handled independently.
    """

    grouped: dict[str, list[Mapping[str, Any]]] = {}

    for row in rows:
        athlete_id = _athlete_id(row)

        grouped.setdefault(
            athlete_id,
            [],
        ).append(row)

    examples: list[AthleteHistoryExample] = []

    for athlete_id in sorted(grouped):
        athlete_rows = sorted(
            grouped[athlete_id],
            key=_sort_key,
        )

        history: list[Mapping[str, Any]] = []

        for target_row in athlete_rows:
            if history:
                features = build_historical_features(
                    history
                )

                target = extract_next_competition_target(
                    target_row
                )

                examples.append(
                    AthleteHistoryExample(
                        athlete_id=athlete_id,
                        target_year=_year(
                            target_row
                        ),
                        target_competition=_competition_name(
                            target_row
                        ),
                        features=features,
                        target=target,
                    )
                )

            history.append(target_row)

    return examples


def history_example_to_dict(
    example: AthleteHistoryExample,
) -> dict[str, Any]:
    """
    Convert one history example into a serializable dictionary.
    """

    return {
        "athlete_id": example.athlete_id,
        "target_year": example.target_year,
        "target_competition": (
            example.target_competition
        ),
        "features": features_to_dict(
            example.features
        ),
        "target": target_to_dict(
            example.target
        ),
    }