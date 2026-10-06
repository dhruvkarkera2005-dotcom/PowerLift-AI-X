from pathlib import Path

from powerlift_ai_x.parsing.format4_parser import (
    detect_format4_weight_class_section,
    parse_format4_row,
    parse_format4_text,
)


def read_extracted(name: str) -> str:
    return Path(
        "data/extracted"
    ).joinpath(name).read_text(
        encoding="utf-8",
        errors="replace",
    )


def test_detect_format4_master_weight_class():
    result = detect_format4_weight_class_section(
        "Master 1 - 59kg"
    )

    assert result == (
        "59",
        "Master 1",
    )


def test_detect_format4_master2_weight_class():
    result = detect_format4_weight_class_section(
        "Master 2 - 74kg"
    )

    assert result == (
        "74",
        "Master 2",
    )


def test_parse_format4_real_row():
    line = (
        "1 Poonnusami VELAYUTHAM 1980 T N 14 "
        "57.20 0.168244 "
        "130.0 145.0 147.5 147.5 [1] "
        "70.0 80.0 85.0 85.0 [1] "
        "160.0 180.0 195.0 160.0 [1] "
        "392.5 12 66.035770 38"
    )

    row = parse_format4_row(line)

    assert row is not None
    assert row.place == 1
    assert row.athlete_name == "Poonnusami VELAYUTHAM"
    assert row.bodyweight == 57.20

    assert row.best_squat == 147.5
    assert row.best_bench == 85.0
    assert row.best_deadlift == 160.0

    assert row.total == 392.5
    assert row.status == "PARSED"


def test_parse_format4_multi_token_team():
    line = (
        "2 Rupesh CHAVAN 1984 MAH 13 "
        "57.00 0.168561 "
        "137.5 142.5 145.0 145.0 [2] "
        "67.5 67.5 75.0 75.0 [3] "
        "135.0 150.0 0 157.5 157.5 [2] "
        "377.5 9 63.631778 45"
    )

    row = parse_format4_row(line)

    assert row is not None
    assert row.athlete_name == "Rupesh CHAVAN"
    assert row.bodyweight == 57.00

    assert row.best_squat == 145.0
    assert row.best_bench == 75.0
    assert row.best_deadlift == 157.5

    assert row.total == 377.5


def test_parse_format4_incomplete_row():
    line = (
        "- TEST ATHLETE 1980 KAR 1 "
        "57.20 0.168244 "
        "130.0 140.0 X 140.0 [1] "
        "70.0 X X - [1] "
        "X X X - [1] "
        "- - -"
    )

    row = parse_format4_row(line)

    assert row is not None
    assert row.place is None

    assert row.best_squat == 140.0
    assert row.best_bench is None
    assert row.best_deadlift is None

    assert row.total is None
    assert row.status == "INCOMPLETE"


def test_parse_format4_real_file():
    text = read_extracted(
        "_National_Masters_Classic_Powerlifting_Championship_2026_M_024535.txt"
    )

    results = parse_format4_text(text)

    assert len(results) > 0

    first = results[0]

    assert first["weight_class"] == "59"
    assert first["division"] == "Master 1"

    row = first["row"]

    assert row.athlete_name == "Poonnusami VELAYUTHAM"
    assert row.bodyweight == 57.20

    assert row.best_squat == 147.5
    assert row.best_bench == 85.0
    assert row.best_deadlift == 160.0

    assert row.total == 392.5