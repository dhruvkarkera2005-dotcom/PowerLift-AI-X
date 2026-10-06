from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from powerlift_ai_x.identity.resolver import (
    IdentityCandidate,
    IdentityDecision,
    resolve_identity_pair,
)


INPUT_PATH = Path(
    "data/final/competition_results.jsonl"
)

OUTPUT_PATH = Path(
    "data/final/athlete_identity_resolution.json"
)


def load_rows(
    path: Path,
) -> list[dict]:
    """
    Load canonical CompetitionResult records.
    """

    return [
        json.loads(line)
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]


def make_candidate(
    row: dict,
) -> IdentityCandidate:
    """
    Convert one canonical record into an
    identity-resolution candidate.
    """

    return IdentityCandidate(
        athlete_id=row["athlete_id"],
        date_of_birth=row.get(
            "date_of_birth"
        ),
        team=row.get("team"),
        lot=row.get("lot"),
        bodyweight=row.get(
            "bodyweight"
        ),
        division=row["division"],
        weight_class=row["weight_class"],
        equipment=row["equipment"],
    )


def resolve_group(
    key: tuple,
    rows: list[dict],
) -> dict:
    """
    Resolve one same-athlete/year/competition
    collision group.

    The current resolver is pairwise. Every pair
    must agree before the group can be classified
    as SAME or SPLIT.

    If the available evidence is insufficient,
    the group remains UNRESOLVED.
    """

    athlete_id, year, competition = key

    candidates = [
        make_candidate(row)
        for row in rows
    ]

    decisions: list[
        tuple[
            IdentityDecision,
            str,
        ]
    ] = []

    for index in range(
        len(candidates)
    ):
        for other_index in range(
            index + 1,
            len(candidates),
        ):
            result = resolve_identity_pair(
                candidates[index],
                candidates[other_index],
            )

            decisions.append(
                (
                    result.decision,
                    result.reason,
                )
            )

    decision_values = [
        decision
        for decision, _ in decisions
    ]

    reasons = Counter(
        reason
        for _, reason in decisions
    )

    if (
        decision_values
        and all(
            decision
            == IdentityDecision.SAME
            for decision in decision_values
        )
    ):
        classification = (
            IdentityDecision.SAME
        )

    elif any(
        decision
        == IdentityDecision.SPLIT
        for decision in decision_values
    ):
        classification = (
            IdentityDecision.SPLIT
        )

    else:
        classification = (
            IdentityDecision.UNRESOLVED
        )

    return {
        "athlete_id": athlete_id,
        "year": year,
        "competition": competition,
        "records": len(rows),
        "classification": classification.value,
        "reasons": dict(reasons),
        "dobs": sorted(
            {
                row["date_of_birth"]
                for row in rows
                if row.get("date_of_birth")
            }
        ),
        "teams": sorted(
            {
                row["team"]
                for row in rows
                if row.get("team")
            }
        ),
        "bodyweights": sorted(
            {
                row["bodyweight"]
                for row in rows
                if row.get("bodyweight")
                is not None
            }
        ),
        "divisions": sorted(
            {
                row["division"]
                for row in rows
                if row.get("division")
            }
        ),
        "weight_classes": sorted(
            {
                row["weight_class"]
                for row in rows
                if row.get("weight_class")
            }
        ),
        "equipment": sorted(
            {
                row["equipment"]
                for row in rows
                if row.get("equipment")
            }
        ),
    }


def build_collision_groups(
    rows: list[dict],
) -> dict[tuple, list[dict]]:
    """
    Group records by the current candidate identity,
    competition year, and competition.

    This does NOT modify athlete IDs.
    """

    groups: dict[
        tuple,
        list[dict],
    ] = defaultdict(list)

    for row in rows:

        key = (
            row["athlete_id"],
            row["year"],
            row["competition"],
        )

        groups[key].append(row)

    return {
        key: values
        for key, values in groups.items()
        if len(values) > 1
    }


def main() -> None:

    rows = load_rows(
        INPUT_PATH
    )

    collision_groups = (
        build_collision_groups(rows)
    )

    reports = [
        resolve_group(
            key,
            values,
        )
        for key, values
        in sorted(
            collision_groups.items(),
            key=lambda item: (
                item[0][1],
                item[0][2],
                item[0][0],
            ),
        )
    ]

    summary = Counter(
        report["classification"]
        for report in reports
    )

    total_records = sum(
        report["records"]
        for report in reports
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "schema_version": 1,
        "source": str(INPUT_PATH),
        "total_collision_groups": len(
            reports
        ),
        "total_records_in_collision_groups": (
            total_records
        ),
        "classification_counts": dict(
            summary
        ),
        "groups": reports,
    }

    OUTPUT_PATH.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("=" * 40)
    print("ATHLETE IDENTITY RESOLUTION")
    print("=" * 40)
    print(
        "CANONICAL RECORDS:",
        len(rows),
    )
    print(
        "COLLISION GROUPS:",
        len(reports),
    )
    print(
        "RECORDS IN COLLISIONS:",
        total_records,
    )
    print()

    for decision in IdentityDecision:
        print(
            f"{decision.value}:",
            summary.get(
                decision.value,
                0,
            ),
        )

    print()
    print(
        "OUTPUT:",
        OUTPUT_PATH,
    )
    print("=" * 40)


if __name__ == "__main__":
    main()