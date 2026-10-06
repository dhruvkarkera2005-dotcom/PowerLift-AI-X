from pathlib import Path

from powerlift_ai_x.parsing.format3_parser import (
    detect_format3_weight_class_section,
    parse_format3_row,
    parse_format3_text,
)


def read_extracted(name: str) -> str:
    return Path(
        "data/extracted"
    ).joinpath(name).read_text(
        encoding="utf-8",
        errors="replace",
    )


def test_detect_format3_weight_class():
    result = detect_format3_weight_class_section(
        "Open - 59kg"
    )

    assert result == (
        "59",
        "Open",
    )


def test_detect_format3_subjunior():
    result = detect_format3_weight_class_section(
        "Sub Junior - 66kg"
    )

    assert result == (
        "66",
        "Sub Junior",
    )


def test_parse_format3_real_row():
    line = (
        "1 HALESH NAYAK 25-01-2000 KAR 13 "
        "58.50 0.146559 "
        "190.0 205.0 217.5 205.0 [2] "
        "110.0 117.5 122.5 117.5 [1] "
        "190.0 202.5 217.5 202.5 [1] "
        "525.0 12 76.943475 13"
    )

    row = parse_format3_row(line)

    assert row is not None
    assert row.place == 1
    assert row.athlete_name == "HALESH NAYAK"
    assert row.bodyweight == 58.50

    assert row.best_squat == 205.0
    assert row.best_bench == 117.5
    assert row.best_deadlift == 202.5

    assert row.total == 525.0
    assert row.status == "PARSED"


def test_parse_format3_multi_token_team():
    line = (
        "2 SAMUEL VASANTH 11-11-2004 T N 9 "
        "59.00 0.145591 "
        "200.0 215.0 220.0 220.0 [2] "
        "100.0 110.0 115.0 115.0 [2] "
        "210.0 230.0 250.0 210.0 [1] "
        "545.0 9 79.347095 21"
    )

    row = parse_format3_row(line)

    assert row is not None
    assert row.athlete_name == "SAMUEL VASANTH"
    assert row.bodyweight == 59.00
    assert row.best_squat == 220.0
    assert row.best_bench == 115.0
    assert row.best_deadlift == 210.0
    assert row.total == 545.0


def test_parse_format3_incomplete_row():
    line = (
        "- TEST ATHLETE 01-01-2000 KAR 1 "
        "58.50 0.146559 "
        "190.0 200.0 X 190.0 [1] "
        "100.0 X X - [1] "
        "X X X - [1] "
        "- - -"
    )

    row = parse_format3_row(line)

    assert row is not None
    assert row.place is None
    assert row.best_squat == 190.0
    assert row.best_bench is None
    assert row.best_deadlift is None
    assert row.total is None
    assert row.status == "INCOMPLETE"


def test_parse_format3_real_file():
    text = read_extracted(
        "20241124011317ab.txt"
    )

    results = parse_format3_text(text)

    assert len(results) > 0

    first = results[0]

    assert first["gender"] == "Men"
    assert first["weight_class"] == "59"
    assert first["division"] == "Open"

    row = first["row"]

    assert row.athlete_name == "HALESH NAYAK"
    assert row.best_squat == 205.0
    assert row.best_bench == 117.5
    assert row.best_deadlift == 202.5
    assert row.total == 525.0
def test_parse_format3_ignores_best_lifter_and_team_championship():
    text = """
Men
Sub Junior - 120kg
Place Name DOB Team Lot Bd. Wt. Coeff. SQ1 SQ2 SQ3 SQ [PL] BP1 BP2 BP3 BP [PL] DL1 DL2 DL3 DL [PL] Total Points IPF GL Points Place
1 PRITHVIRAJ SHINDE 30-10-2006 MAH 266 116.20 0.117903 220.0 230.0 240.0 240.0 [1] 120.0 130.0 135.0 135.0 [2] 225.0 235.0 260.0 260.0 [1] 635.0 12 74.868405 16

Best Lifter - Sub Junior
Place Name Team Wt.Cat. Bd.Wt. Coeff. Total IPF GL Points
1 SOHEL ESHAN JHA 74kg 72.35 0.148542 565.0 83.926230
2 ABHISHEK TRIPATHI U P 83kg 82.65 0.138723 600.0 83.233800

Team Championship - Sub Junior
Place Team Points Best Points IPF GL Points
1 MADHYA PRADESH 41 12+9+7+7+6 347.693815

Junior - 53kg
Place Name DOB Team Lot Bd. Wt. Coeff. SQ1 SQ2 SQ3 SQ [PL] BP1 BP2 BP3 BP [PL] DL1 DL2 DL3 DL [PL] Total Points IPF GL Points Place
1 TEST JUNIOR 01-01-2005 MAH 1 52.00 0.170000 100.0 110.0 120.0 120.0 [1] 60.0 65.0 70.0 70.0 [1] 130.0 140.0 150.0 150.0 [1] 340.0 12 70.000000 1
"""

    results = parse_format3_text(text)

    assert len(results) == 2

    first = results[0]
    second = results[1]

    assert first["row"].athlete_name == "PRITHVIRAJ SHINDE"
    assert first["row"].total == 635.0
    assert first["weight_class"] == "120"
    assert first["division"] == "Sub Junior"

    assert second["row"].athlete_name == "TEST JUNIOR"
    assert second["row"].total == 340.0
    assert second["weight_class"] == "53"
    assert second["division"] == "Junior"


def test_parse_format3_best_lifter_rows_are_not_result_rows():
    text = """
Men
Open - 59kg
Best Lifter - Open
Place Name Team Wt.Cat. Bd.Wt. Coeff. Total IPF GL Points
1 TEST ATHLETE 59kg 58.00 0.145000 500.0 70.000000
"""

    results = parse_format3_text(text)

    assert results == []