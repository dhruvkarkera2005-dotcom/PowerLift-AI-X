from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from powerlift_ai_x.identity.assignment import (
    make_resolved_athlete_id,
)


def load_resolution_report(
    path: str | Path,
) -> dict[str, Any]:
    """
    Load the athlete identity resolution report.
    """

    path = Path(path)

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def _group_key(
    athlete_id: str,
    year: int,
    competition: str,
) -> tuple[str, int, str]:
    """
    Build the canonical collision-group key.
    """

    return (
        athlete_id,
        year,
        competition,
    )


def build_resolution_index(
    report: dict[str, Any],
) -> dict[tuple[str, int, str], dict[str, Any]]:
    """
    Index resolution groups for deterministic lookup.
    """

    index: dict[
        tuple[str, int, str],
        dict[str, Any],
    ] = {}

    for group in report.get(
        "groups",
        [],
    ):
        key = _group_key(
            group["athlete_id"],
            int(group["year"]),
            group["competition"],
        )

        index[key] = group

    return index


def apply_identity_resolution(
    record: dict[str, Any],
    resolution_index: dict[
        tuple[str, int, str],
        dict[str, Any],
    ],
) -> dict[str, Any]:
    """
    Apply resolved identity metadata to one canonical record.

    Existing athlete_id is preserved.

    Records with DOB receive a deterministic
    NAME + DOB resolved identity.

    Records without DOB retain their candidate
    athlete_id and receive CANDIDATE confidence.
    """

    result = dict(record)

    athlete_id = record["athlete_id"]

    year = int(
        record["year"]
    )

    competition = record[
        "competition"
    ]

    dob = record.get(
        "date_of_birth"
    )

    group = resolution_index.get(
        _group_key(
            athlete_id,
            year,
            competition,
        )
    )

    # --------------------------------------------------------
    # Strong identity evidence: DOB available.
    # --------------------------------------------------------

    if dob:
        resolved = make_resolved_athlete_id(
            athlete_name=record.get(
                "athlete_name",
                "",
            )
            or record.get(
                "name",
                "",
            )
            or _recover_name_from_candidate(
                record
            ),
            date_of_birth=dob,
        )

        result[
            "resolved_athlete_id"
        ] = resolved.resolved_athlete_id

        result[
            "identity_confidence"
        ] = resolved.confidence

        return result

    # --------------------------------------------------------
    # No DOB.
    #
    # Do not invent an identity.
    # --------------------------------------------------------

    result[
        "resolved_athlete_id"
    ] = athlete_id

    result[
        "identity_confidence"
    ] = "CANDIDATE"

    return result


def _recover_name_from_candidate(
    record: dict[str, Any],
) -> str:
    """
    Recover the normalized name when the canonical record
    does not explicitly store it.

    The current canonical schema does not contain athlete_name,
    so this function cannot reverse a name-only hash.

    It therefore raises instead of silently generating an
    incorrect identity.
    """

    raise ValueError(
        "Cannot generate resolved identity from DOB because "
        "canonical record does not contain athlete_name. "
        "Add athlete_name to the canonical model before "
        "applying resolved identities."
    )
