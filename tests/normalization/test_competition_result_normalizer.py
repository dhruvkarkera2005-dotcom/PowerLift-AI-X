from powerlift_ai_x.models.enums import Equipment
from powerlift_ai_x.normalization.competition_result_normalizer import (
    infer_equipment,
    load_source_manifest,
    make_athlete_id,
    normalize_athlete_name,
    normalize_directory,
    normalize_source,
)
from powerlift_ai_x.parsing.unified_parser import parse_file


def test_normalize_athlete_name():
    assert (
        normalize_athlete_name(
            "  SUNIL   PARASHARAM KONEWADKAR  "
        )
        == "SUNIL PARASHARAM KONEWADKAR"
    )


def test_make_athlete_id_is_deterministic():
    first = make_athlete_id(
        "SUNIL PARASHARAM KONEWADKAR"
    )

    second = make_athlete_id(
        "SUNIL PARASHARAM KONEWADKAR"
    )

    assert first == second
    assert first.startswith("ATH-")


def test_infer_equipment():
    assert (
        infer_equipment(
            "National Senior Classic Powerlifting Championship"
        )
        == Equipment.CLASSIC
    )

    assert (
        infer_equipment(
            "National Senior Equipped Powerlifting Championship"
        )
        == Equipment.EQUIPPED
    )


def test_normalize_real_dataset():
    results = normalize_directory(
        "data/extracted",
        "data/final_source_manifest.json",
    )

    assert results

    assert all(
        result.athlete_id
        for result in results
    )

    assert all(
        result.competition
        for result in results
    )

    assert all(
        result.year
        for result in results
    )

    assert all(
        result.division
        for result in results
    )

    assert all(
        result.weight_class
        for result in results
    )


def test_normalize_known_sunil_result():
    # --------------------------------------------------------
    # Use the exact source containing the verified Sunil row.
    #
    # This is FORMAT1:
    #
    # National Senior Equipped Powerlifting  Championship 2018
    #
    # Sunil:
    #
    # 66kg - Open
    # Place = 5
    # Bodyweight = 65.95
    #
    # SQ: 250.0 / 262.5 / 262.5
    # Best SQ: 262.5
    #
    # BP: 140.0 / 147.5 / 155.0
    # Best BP: 155.0
    #
    # DL: 242.5 / 252.5 / 265.0
    # Best DL: 252.5
    #
    # Total: 670.0
    # --------------------------------------------------------

    source = parse_file(
        "data/extracted/20210909050642ab.txt"
    )

    assert source.detected_format == "FORMAT1"

    parsed = [
        result
        for result in source.results
        if (
            result.get("status") == "PARSED"
            and result.get("row") is not None
            and "SUNIL PARASHARAM"
            in result["row"].athlete_name
        )
    ]

    assert len(parsed) == 1

    parsed_result = parsed[0]

    assert parsed_result["weight_class"] == "66"
    assert parsed_result["division"] == "Open"

    parsed_row = parsed_result["row"]

    assert parsed_row.place == 5

    assert parsed_row.athlete_name == (
        "SUNIL PARASHARAM KONEWADKAR"
    )

    assert parsed_row.bodyweight == 65.95

    assert parsed_row.squat_attempt_1 == 250.0
    assert parsed_row.squat_attempt_2 == 262.5
    assert parsed_row.squat_attempt_3 == 262.5
    assert parsed_row.best_squat == 262.5

    assert parsed_row.bench_attempt_1 == 140.0
    assert parsed_row.bench_attempt_2 == 147.5
    assert parsed_row.bench_attempt_3 == 155.0
    assert parsed_row.best_bench == 155.0

    assert parsed_row.deadlift_attempt_1 == 242.5
    assert parsed_row.deadlift_attempt_2 == 252.5
    assert parsed_row.deadlift_attempt_3 == 265.0
    assert parsed_row.best_deadlift == 252.5

    assert parsed_row.total == 670.0

    # --------------------------------------------------------
    # Normalize using the exact matching manifest entry.
    # --------------------------------------------------------

    manifest = load_source_manifest(
        "data/final_source_manifest.json"
    )

    metadata = manifest[
        "20210909050642ab.pdf"
    ]

    normalized = normalize_source(
        source,
        metadata,
    )

    matches = [
        row
        for row in normalized
        if row.athlete_id
        == make_athlete_id(
            "SUNIL PARASHARAM KONEWADKAR"
        )
    ]

    assert len(matches) == 1

    row = matches[0]

    # --------------------------------------------------------
    # Canonical metadata
    # --------------------------------------------------------

    assert row.athlete_id == (
        make_athlete_id(
            "SUNIL PARASHARAM KONEWADKAR"
        )
    )

    assert row.competition == (
        "National Senior Equipped Powerlifting  Championship 2018"
    )

    assert row.year == 2018

    assert row.weight_class == "66"
    assert row.division == "Open"

    assert row.equipment == Equipment.EQUIPPED

    # --------------------------------------------------------
    # Athlete result
    # --------------------------------------------------------

    assert row.bodyweight == 65.95
    assert row.place == 5

    # Squat

    assert row.squat_1 == 250.0
    assert row.squat_2 == 262.5
    assert row.squat_3 == 262.5
    assert row.best_squat == 262.5

    # Bench

    assert row.bench_1 == 140.0
    assert row.bench_2 == 147.5
    assert row.bench_3 == 155.0
    assert row.best_bench == 155.0

    # Deadlift

    assert row.deadlift_1 == 242.5
    assert row.deadlift_2 == 252.5
    assert row.deadlift_3 == 265.0
    assert row.best_deadlift == 252.5

    # Total

    assert row.total == 670.0