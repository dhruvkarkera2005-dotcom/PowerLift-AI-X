import pytest

from powerlift_ai_x.parsing.result_parser import (
    best_attempt,
    build_parsed_row,
    clean_number,
    parse_place,
)


def test_clean_number_success():
    assert clean_number("170") == 170.0
    assert clean_number("170.5") == 170.5


def test_clean_number_failed_attempt():
    assert clean_number("X170") == -170.0
    assert clean_number("x170") == -170.0


def test_clean_number_missing():
    assert clean_number("-") is None
    assert clean_number("X") is None
    assert clean_number("") is None


def test_best_attempt_ignores_failed_attempts():
    assert best_attempt(
        [-170.0, 180.0, -190.0]
    ) == 180.0


def test_best_attempt_all_failed():
    assert best_attempt(
        [-170.0, -180.0, -190.0]
    ) is None


def test_parse_place():
    assert parse_place("1") == 1
    assert parse_place("15") == 15
    assert parse_place("DSQ") is None


def test_build_parsed_row():
    row = build_parsed_row(
        place="1",
        athlete_name="TEST ATHLETE",
        bodyweight="74.5",
        squat=["180", "190", "X200"],
        bench=["120", "127.5", "X130"],
        deadlift=["200", "210", "X220"],
        total="527.5",
    )

    assert row.place == 1
    assert row.athlete_name == "TEST ATHLETE"
    assert row.bodyweight == 74.5

    assert row.best_squat == 190.0
    assert row.best_bench == 127.5
    assert row.best_deadlift == 210.0

    assert row.total == 527.5
    assert row.status == "PARSED"
from pathlib import Path

from powerlift_ai_x.parsing.result_parser import (
    detect_weight_class_section,
    parse_format1_row,
    parse_format1_text,
)


def test_detect_weight_class_section():
    assert detect_weight_class_section(
        "59kg - Open"
    ) == ("59", "Open")

    assert detect_weight_class_section(
        "74kg - Open"
    ) == ("74", "Open")


def test_parse_format1_real_row():
    line = (
        "1 PANNEERASELVAM S 13-08-1991 "
        "PUD 62 58.80 "
        "170.0 190.0 200.0 200.0 [1] "
        "110.0 120.0 120.0 120.0 [3] "
        "200.0 222.5 232.5 232.5 [1] "
        "552.5 12"
    )

    row = parse_format1_row(line)

    assert row is not None
    assert row.place == 1
    assert row.athlete_name == "PANNEERASELVAM S"
    assert row.bodyweight == 58.8

    assert row.best_squat == 200.0
    assert row.best_bench == 120.0
    assert row.best_deadlift == 232.5
    assert row.total == 552.5


def test_parse_format1_failed_attempt():
    line = (
        "7 MOHAMMED AARIF 30-10-1991 "
        "GUJ 68 57.25 "
        "140.0 140.0 155.0 155.0 [7] "
        "100.0 102.5 X 102.5 [4] "
        "175.0 175.0 180.0 175.0 [7] "
        "432.5 4"
    )

    row = parse_format1_row(line)

    assert row is not None
    assert row.best_bench == 102.5


def test_parse_format1_sections():
    text = """
59kg - Open
1 PANNEERASELVAM S 13-08-1991 PUD 62 58.80 170.0 190.0 200.0 200.0 [1] 110.0 120.0 120.0 120.0 [3] 200.0 222.5 232.5 232.5 [1] 552.5 12
"""

    results = parse_format1_text(text)

    assert len(results) == 1
    assert results[0]["status"] == "PARSED"
    assert results[0]["weight_class"] == "59"
    assert results[0]["division"] == "Open"

    row = results[0]["row"]

    assert row.place == 1
    assert row.athlete_name == "PANNEERASELVAM S"
    assert row.bodyweight == 58.8
    assert row.best_squat == 200.0
    assert row.best_bench == 120.0
    assert row.best_deadlift == 232.5
    assert row.total == 552.5
def test_parse_format1_multi_token_team():
    line = (
        "4 DHUEV NAIK 05-12-1994 "
        "M P 123 65.40 "
        "160.0 165.0 167.5 160.0 [6] "
        "117.5 122.5 125.0 122.5 [3] "
        "220.0 230.0 232.5 220.0 [1] "
        "502.5 7"
    )

    row = parse_format1_row(line)

    assert row is not None
    assert row.place == 4
    assert row.athlete_name == "DHUEV NAIK"
    assert row.bodyweight == 65.4

    assert row.best_squat == 160.0
    assert row.best_bench == 122.5
    assert row.best_deadlift == 220.0
    assert row.total == 502.5


def test_parse_format1_master_multi_token_team():
    line = (
        "1 DILEEP SHARMA 10-08-1979 "
        "M P 47 57.80 "
        "110.0 120.0 125.0 125.0 [3] "
        "90.0 97.5 102.5 102.5 [1] "
        "170.0 180.0 185.0 185.0 [1] "
        "412.5 12"
    )

    row = parse_format1_row(line)

    assert row is not None
    assert row.place == 1
    assert row.athlete_name == "DILEEP SHARMA"
    assert row.bodyweight == 57.8

    assert row.best_squat == 125.0
    assert row.best_bench == 102.5
    assert row.best_deadlift == 185.0
    assert row.total == 412.5
def test_parse_format1_incomplete_unranked_row():
    line = (
        "- P RAJU 01-08-1962 TEL 115 73.25 "
        "130.0 - 65.0 - 145.0 - - -"
    )

    row = parse_format1_row(line)

    assert row is not None
    assert row.place is None
    assert row.athlete_name == "P RAJU"
    assert row.bodyweight == 73.25

    assert row.best_squat == 130.0
    assert row.best_bench == 65.0
    assert row.best_deadlift == 145.0

    assert row.total is None
    assert row.status == "INCOMPLETE"