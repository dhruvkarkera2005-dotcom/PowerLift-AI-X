import json

from powerlift_ai_x.dataset.writer import (
    CANONICAL_FIELDS,
    competition_result_to_dict,
    write_canonical_dataset,
    write_csv,
    write_jsonl,
)
from powerlift_ai_x.models.competition_result import (
    CompetitionResult,
)
from powerlift_ai_x.models.enums import Equipment


def make_result() -> CompetitionResult:
    return CompetitionResult(
        athlete_id="ATH-test123",
        competition="Test Competition",
        year=2026,
        division="Open",
        weight_class="66",
        equipment=Equipment.CLASSIC,
        bodyweight=65.5,

        squat_1=200.0,
        squat_2=210.0,
        squat_3=215.0,
        best_squat=210.0,

        bench_1=120.0,
        bench_2=125.0,
        bench_3=127.5,
        best_bench=125.0,

        deadlift_1=220.0,
        deadlift_2=230.0,
        deadlift_3=235.0,
        best_deadlift=230.0,

        total=565.0,
        place=1,
    )


def test_competition_result_to_dict():
    result = make_result()

    data = competition_result_to_dict(
        result
    )

    assert isinstance(data, dict)

    assert data["athlete_id"] == "ATH-test123"
    assert data["competition"] == "Test Competition"
    assert data["year"] == 2026
    assert data["weight_class"] == "66"
    assert data["equipment"] == "CLASSIC"

    assert data["best_squat"] == 210.0
    assert data["best_bench"] == 125.0
    assert data["best_deadlift"] == 230.0
    assert data["total"] == 565.0


def test_write_jsonl(tmp_path):
    result = make_result()

    output = (
        tmp_path
        / "results.jsonl"
    )

    count = write_jsonl(
        [result],
        output,
    )

    assert count == 1
    assert output.exists()

    lines = output.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    data = json.loads(lines[0])

    assert data["athlete_id"] == (
        "ATH-test123"
    )

    assert data["best_squat"] == 210.0


def test_write_csv(tmp_path):
    result = make_result()

    output = (
        tmp_path
        / "results.csv"
    )

    count = write_csv(
        [result],
        output,
    )

    assert count == 1
    assert output.exists()

    text = output.read_text(
        encoding="utf-8"
    )

    lines = text.splitlines()

    assert len(lines) == 2

    header = lines[0].split(",")

    assert header == CANONICAL_FIELDS

    assert "ATH-test123" in lines[1]
    assert "Test Competition" in lines[1]


def test_write_canonical_dataset(tmp_path):
    results = [
        make_result(),
        make_result().model_copy(
            update={
                "athlete_id": "ATH-test456",
                "place": 2,
            }
        ),
    ]

    output_directory = (
        tmp_path / "final"
    )

    metadata = write_canonical_dataset(
        results,
        output_directory,
    )

    assert metadata["row_count"] == 2

    jsonl = (
        output_directory
        / "competition_results.jsonl"
    )

    csv = (
        output_directory
        / "competition_results.csv"
    )

    assert jsonl.exists()
    assert csv.exists()

    assert len(
        jsonl.read_text(
            encoding="utf-8"
        ).splitlines()
    ) == 2

    assert len(
        csv.read_text(
            encoding="utf-8"
        ).splitlines()
    ) == 3