from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from powerlift_ai_x.models.competition_result import (
    CompetitionResult,
)


# ============================================================
# SERIALIZATION
# ============================================================

def competition_result_to_dict(
    result: CompetitionResult,
) -> dict:
    """
    Convert one CompetitionResult into a plain dictionary.

    Pydantic's model_dump() is used so the output contains
    only canonical model fields.
    """

    return result.model_dump(
        mode="json"
    )


# ============================================================
# JSONL
# ============================================================

def write_jsonl(
    results: Iterable[CompetitionResult],
    output_path: str | Path,
) -> int:
    """
    Write CompetitionResult objects to a JSON Lines file.

    One result is written per line.

    Returns:
        Number of rows written.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    count = 0

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        for result in results:
            payload = competition_result_to_dict(
                result
            )

            file.write(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )

            file.write("\n")

            count += 1

    return count


# ============================================================
# CSV
# ============================================================

CANONICAL_FIELDS = [
    "athlete_id",
    "competition",
    "year",
    "division",
    "weight_class",
    "equipment",
    "bodyweight",

    "squat_1",
    "squat_2",
    "squat_3",
    "best_squat",

    "bench_1",
    "bench_2",
    "bench_3",
    "best_bench",

    "deadlift_1",
    "deadlift_2",
    "deadlift_3",
    "best_deadlift",

    "total",
    "place",
]


def write_csv(
    results: Iterable[CompetitionResult],
    output_path: str | Path,
) -> int:
    """
    Write CompetitionResult objects to CSV.

    The column order is fixed using CANONICAL_FIELDS.

    Returns:
        Number of rows written.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    count = 0

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=CANONICAL_FIELDS,
            extrasaction="ignore",
        )

        writer.writeheader()

        for result in results:
            payload = competition_result_to_dict(
                result
            )

            writer.writerow(
                {
                    field: payload.get(field)
                    for field in CANONICAL_FIELDS
                }
            )

            count += 1

    return count


# ============================================================
# CANONICAL DATASET
# ============================================================

def write_canonical_dataset(
    results: Iterable[CompetitionResult],
    output_directory: str | Path,
) -> dict[str, object]:
    """
    Write the canonical normalized dataset.

    Creates:

        competition_results.jsonl
        competition_results.csv

    Returns metadata describing the files written.
    """

    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Materialize once because results may be a generator.
    materialized = list(results)

    jsonl_path = (
        output_directory
        / "competition_results.jsonl"
    )

    csv_path = (
        output_directory
        / "competition_results.csv"
    )

    jsonl_count = write_jsonl(
        materialized,
        jsonl_path,
    )

    csv_count = write_csv(
        materialized,
        csv_path,
    )

    if jsonl_count != csv_count:
        raise RuntimeError(
            "JSONL and CSV row counts differ."
        )

    return {
        "row_count": jsonl_count,
        "jsonl_path": str(jsonl_path),
        "csv_path": str(csv_path),
    }