from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class IdentityContext:
    """
    Context describing one competition result for identity analysis.
    """

    athlete_id: str
    year: int
    competition: str
    division: str
    weight_class: str
    equipment: str
    bodyweight: float | None


@dataclass(frozen=True)
class IdentityCollision:
    """
    A name-based athlete ID appearing in multiple contexts
    that cannot safely be treated as one chronological identity.
    """

    athlete_id: str
    contexts: tuple[IdentityContext, ...]


def _to_year(value: Any) -> int:
    if value is None:
        raise ValueError("Missing year")

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid year: {value!r}"
        ) from exc


def _to_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _to_bodyweight(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def make_identity_context(
    row: Mapping[str, Any],
) -> IdentityContext:
    """
    Convert a canonical competition row into identity context.
    """

    athlete_id = _to_text(
        row.get("athlete_id")
    )

    if not athlete_id:
        raise ValueError(
            "Missing athlete_id"
        )

    return IdentityContext(
        athlete_id=athlete_id,
        year=_to_year(row.get("year")),
        competition=_to_text(
            row.get("competition")
        ),
        division=_to_text(
            row.get("division")
        ),
        weight_class=_to_text(
            row.get("weight_class")
        ),
        equipment=_to_text(
            row.get("equipment")
        ),
        bodyweight=_to_bodyweight(
            row.get("bodyweight")
        ),
    )


def find_identity_collisions(
    rows: Sequence[Mapping[str, Any]],
) -> list[IdentityCollision]:
    """
    Find name-based athlete IDs that appear in multiple
    competition contexts.

    This function deliberately DOES NOT decide that two rows
    represent different people.

    It only identifies candidate collision groups for review.
    """

    grouped: dict[
        str,
        set[IdentityContext],
    ] = defaultdict(set)

    for row in rows:
        context = make_identity_context(row)

        grouped[
            context.athlete_id
        ].add(context)

    collisions: list[IdentityCollision] = []

    for athlete_id in sorted(grouped):
        contexts = grouped[athlete_id]

        if len(contexts) > 1:
            collisions.append(
                IdentityCollision(
                    athlete_id=athlete_id,
                    contexts=tuple(
                        sorted(
                            contexts,
                            key=lambda x: (
                                x.year,
                                x.competition,
                                x.division,
                                x.weight_class,
                                x.equipment,
                                x.bodyweight
                                if x.bodyweight
                                is not None
                                else float("-inf"),
                            ),
                        )
                    ),
                )
            )

    return collisions


def find_same_competition_collisions(
    rows: Sequence[Mapping[str, Any]],
) -> list[IdentityCollision]:
    """
    Find athlete IDs occurring more than once in the same
    year + competition.

    These groups require special handling because they cannot
    automatically be interpreted as chronological progression.
    """

    grouped: dict[
        tuple[str, int, str],
        list[IdentityContext],
    ] = defaultdict(list)

    for row in rows:
        context = make_identity_context(row)

        key = (
            context.athlete_id,
            context.year,
            context.competition,
        )

        grouped[key].append(context)

    collisions: list[IdentityCollision] = []

    for (
        athlete_id,
        year,
        competition,
    ), contexts in sorted(grouped.items()):
        unique_contexts = tuple(
            sorted(
                set(contexts),
                key=lambda x: (
                    x.division,
                    x.weight_class,
                    x.equipment,
                    x.bodyweight
                    if x.bodyweight is not None
                    else float("-inf"),
                ),
            )
        )

        if len(contexts) > 1:
            collisions.append(
                IdentityCollision(
                    athlete_id=athlete_id,
                    contexts=unique_contexts,
                )
            )

    return collisions


def collision_statistics(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, int]:
    """
    Return conservative identity-collision statistics.
    """

    collisions = find_identity_collisions(rows)
    same_competition = (
        find_same_competition_collisions(rows)
    )

    return {
        "athlete_ids": len(
            {
                _to_text(row.get("athlete_id"))
                for row in rows
            }
        ),
        "candidate_collision_ids": len(
            collisions
        ),
        "same_competition_collision_groups": len(
            same_competition
        ),
    }