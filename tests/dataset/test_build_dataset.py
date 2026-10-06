from pathlib import Path
import json

from powerlift_ai_x.dataset.build_dataset import (
    build_dataset,
)

from powerlift_ai_x.normalization.competition_result_normalizer import (
    make_athlete_id,
)


def test_build_dataset_contains_known_sunil(tmp_path):
    result = build_dataset(
        extracted_directory="data/extracted",
        manifest_path="data/final_source_manifest.json",
        output_directory=tmp_path,
    )

    jsonl_path = Path(
        result["jsonl_path"]
    )

    sunil_id = make_athlete_id(
        "SUNIL PARASHARAM KONEWADKAR"
    )

    matches = []

    with jsonl_path.open(
        encoding="utf-8"
    ) as file:

        for line in file:
            row = json.loads(line)

            if (
                row["athlete_id"]
                == sunil_id
                and row["competition"]
                == (
                    "Federation Cup "
                    "Powerlifting Championship "
                    "2018-19"
                )
            ):
                matches.append(row)

    assert len(matches) == 1

    row = matches[0]

    assert row["year"] == 2019
    assert row["weight_class"] == "66"
    assert row["division"] == "Open"

    assert row["best_squat"] == 260.0
    assert row["best_bench"] == 152.5
    assert row["best_deadlift"] == 247.5
    assert row["total"] == 660.0


def test_build_dataset_real_dataset(tmp_path):
    result = build_dataset(
        extracted_directory="data/extracted",
        manifest_path="data/final_source_manifest.json",
        output_directory=tmp_path,
    )

    assert result["source_count"] == 74

    assert result["normalized_count"] == 9874

    assert result["incomplete_count"] == 1023

    assert result["review_count"] == 0

    jsonl_path = Path(
        result["jsonl_path"]
    )

    csv_path = Path(
        result["csv_path"]
    )

    assert jsonl_path.exists()
    assert csv_path.exists()

    jsonl_lines = (
        jsonl_path
        .read_text(
            encoding="utf-8"
        )
        .splitlines()
    )

    csv_lines = (
        csv_path
        .read_text(
            encoding="utf-8"
        )
        .splitlines()
    )

    assert len(jsonl_lines) == 9874

    # Header + 9874 rows.
    assert len(csv_lines) == 9875