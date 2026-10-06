from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from powerlift_ai_x.identity.assignment import (
    make_resolved_athlete_id,
)


# ============================================================
# LOAD RESOLUTION REPORT
# ============================================================

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


# ============================================================
# RESOLUTION INDEX
# ============================================================

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
        int(year),
        competition,
    )


def build_resolution_index(
    report: dict[str, Any],
) -> dict[
    tuple[str, int, str],
    dict[str, Any],
]:
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


# ============================================================
# APPLY ONE RECORD
# ============================================================

def apply_identity_resolution(
    record: dict[str, Any],
    resolution_index: dict[
        tuple[str, int, str],
        dict[str, Any],
    ],
) -> dict[str, Any]:
    """
    Apply deterministic resolved identity metadata
    to one canonical competition result.

    The original athlete_id is always preserved.

    Identity rules:

    - DOB available:
        resolved identity = normalized athlete_name + DOB

    - DOB unavailable:
        resolved identity = candidate athlete_id

    Collision groups are used as validation metadata.

    SAME groups naturally collapse to the same
    name + DOB identity.

    SPLIT groups naturally separate when DOBs differ.

    UNRESOLVED groups remain unresolved.
    """

    result = dict(record)

    athlete_id = str(
        record["athlete_id"]
    ).strip()

    year = int(
        record["year"]
    )

    competition = str(
        record["competition"]
    ).strip()

    group = resolution_index.get(
        _group_key(
            athlete_id,
            year,
            competition,
        )
    )

    classification = (
        group.get("classification")
        if group is not None
        else None
    )

    athlete_name = (
        record.get("athlete_name")
        or record.get("name")
    )

    dob = record.get(
        "date_of_birth"
    )

    # --------------------------------------------------------
    # UNRESOLVED
    # --------------------------------------------------------

    if classification == "UNRESOLVED":

        result[
            "resolved_athlete_id"
        ] = None

        result[
            "identity_confidence"
        ] = "UNRESOLVED"

        return result

    # --------------------------------------------------------
    # STRONG IDENTITY:
    #
    # athlete name + DOB
    # --------------------------------------------------------

    if athlete_name and dob:

        resolved = make_resolved_athlete_id(
            athlete_name=str(
                athlete_name
            ),
            date_of_birth=str(
                dob
            ),
        )

        result[
            "resolved_athlete_id"
        ] = (
            resolved.resolved_athlete_id
        )

        if classification == "SAME":

            result[
                "identity_confidence"
            ] = "RESOLVED_SAME"

        elif classification == "SPLIT":

            result[
                "identity_confidence"
            ] = "RESOLVED_SPLIT"

        else:

            result[
                "identity_confidence"
            ] = "HIGH"

        return result

    # --------------------------------------------------------
    # NO DOB
    #
    # Do not invent a cross-record identity.
    # --------------------------------------------------------

    result[
        "resolved_athlete_id"
    ] = athlete_id

    result[
        "identity_confidence"
    ] = "CANDIDATE"

    return result


# ============================================================
# APPLY TO JSONL
# ============================================================

def apply_identity_resolution_file(
    input_path: str | Path,
    resolution_path: str | Path,
    output_path: str | Path,
) -> dict[str, int]:
    """
    Apply identity resolutions to a canonical JSONL file.

    The input file is never modified.
    """

    input_path = Path(
        input_path
    )

    resolution_path = Path(
        resolution_path
    )

    output_path = Path(
        output_path
    )

    report = load_resolution_report(
        resolution_path
    )

    resolution_index = (
        build_resolution_index(
            report
        )
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    total = 0
    high = 0
    same = 0
    split = 0
    candidate = 0
    unresolved = 0

    unique_ids: set[str] = set()

    with (
        input_path.open(
            "r",
            encoding="utf-8",
        ) as source,
        output_path.open(
            "w",
            encoding="utf-8",
        ) as destination,
    ):

        for line in source:

            if not line.strip():
                continue

            record = json.loads(
                line
            )

            resolved = (
                apply_identity_resolution(
                    record,
                    resolution_index,
                )
            )

            destination.write(
                json.dumps(
                    resolved,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )

            total += 1

            resolved_id = resolved.get(
                "resolved_athlete_id"
            )

            if resolved_id:
                unique_ids.add(
                    str(resolved_id)
                )

            confidence = resolved[
                "identity_confidence"
            ]

            if confidence == "HIGH":
                high += 1

            elif confidence == "RESOLVED_SAME":
                same += 1

            elif confidence == "RESOLVED_SPLIT":
                split += 1

            elif confidence == "CANDIDATE":
                candidate += 1

            elif confidence == "UNRESOLVED":
                unresolved += 1

    return {
        "total": total,
        "unique": len(unique_ids),
        "high": high,
        "same": same,
        "split": split,
        "candidate": candidate,
        "unresolved": unresolved,
    }