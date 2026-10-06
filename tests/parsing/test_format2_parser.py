from powerlift_ai_x.parsing.format2_parser import (
    detect_format2_weight_class_section,
    parse_format2_row,
    parse_format2_text,
)
from powerlift_ai_x.parsing.result_parser import (
    tokenize_result_row,
)


def test_detect_format2_weight_class():
    assert detect_format2_weight_class_section(
        "59kg - Open"
    ) == ("59", "Open")


def test_detect_format2_plus_weight_class():
    assert detect_format2_weight_class_section(
        "120+Kg - Open"
    ) == ("120+", "Open")


def test_parse_format2_real_row():
    line = (
        "1 RAJESH SHUKRAWARE 10-05-1983 "
        "M P 15 56.16 0.151379 "
        "230.0 240.0 250.0 240.0 [1] "
        "135.0 142.5 147.5 142.5 [1] "
        "215.0 225.0 230.0 225.0 [1] "
        "607.5 12 91.962743 2"
    )

    row = parse_format2_row(line)

    assert row is not None
    assert row.place == 1
    assert row.athlete_name == "RAJESH SHUKRAWARE"
    assert row.bodyweight == 56.16

    assert row.best_squat == 240.0
    assert row.best_bench == 142.5
    assert row.best_deadlift == 225.0
    assert row.total == 607.5


def test_parse_format2_multi_token_team():
    line = (
        "1 VISHAL GADGE 01-01-1999 "
        "M P 14 82.14 0.116185 "
        "250.0 265.0 275.0 275.0 [2] "
        "165.0 177.5 185.0 185.0 [1] "
        "240.0 252.5 260.0 252.5 [3] "
        "712.5 9 82.781813 6"
    )

    row = parse_format2_row(line)

    assert row is not None
    assert row.athlete_name == "VISHAL GADGE"
    assert row.bodyweight == 82.14
    assert row.best_squat == 275.0
    assert row.best_bench == 185.0
    assert row.best_deadlift == 252.5
    assert row.total == 712.5


def test_parse_format2_failed_attempt():
    line = (
        "1 AKASH SHARMA 20-06-1999 "
        "RAJ 13 82.40 0.115969 "
        "295.0 305.0 312.5 312.5 [1] "
        "170.0 175.0 180.0 175.0 [2] "
        "255.0 262.5 X 262.5 [2] "
        "750.0 12 86.976750 5"
    )

    row = parse_format2_row(line)

    assert row is not None
    assert row.deadlift_attempt_3 is None
    assert row.best_deadlift == 262.5
    assert row.total == 750.0


def test_parse_format2_incomplete_row():
    line = (
        "- YASHWANT GAIKWAD 01-01-2001 "
        "MAH 19 79.70 0.118297 "
        "210.0 220.0 230.0 220.0 [5] "
        "140.0 140.0 140.0 - "
        "X X X - "
        "- - - -"
    )

    row = parse_format2_row(line)

    assert row is not None
    assert row.place is None
    assert row.athlete_name == "YASHWANT GAIKWAD"
    assert row.bodyweight == 79.70

    assert row.best_squat == 220.0
    assert row.best_bench is None
    assert row.best_deadlift is None
    assert row.total is None
    assert row.status == "INCOMPLETE"


def test_parse_format2_ignores_best_lifter_summary():
    line = (
        "1 SHAILENDRA SEVETIYA M P 74kg "
        "72.56 0.125527 752.5 94.459068"
    )

    assert parse_format2_row(line) is None


def test_parse_format2_sections():
    text = """
59kg - Open
1 RAJESH SHUKRAWARE 10-05-1983 M P 15 56.16 0.151379 230.0 240.0 250.0 240.0 [1] 135.0 142.5 147.5 142.5 [1] 215.0 225.0 230.0 225.0 [1] 607.5 12 91.962743 2
"""

    results = parse_format2_text(text)

    assert len(results) == 1
    assert results[0]["weight_class"] == "59"
    assert results[0]["division"] == "Open"
    assert results[0]["status"] == "PARSED"
def test_detect_format2_weight_class_division_first():
    result = detect_format2_weight_class_section(
        "Open - 59kg"
    )

    assert result == (
        "59",
        "Open",
    )


def test_detect_format2_inline_weight_class():
    from powerlift_ai_x.parsing.format2_parser import (
        detect_format2_inline_weight_class,
    )

    tokens = tokenize_result_row(
        "1 SURESH P J&K 59kg 59.00 0.145591 "
        "687.5 100.093813"
    )

    result = detect_format2_inline_weight_class(
        tokens
    )

    assert result is not None
    assert result[1] == "59"
def test_parse_format2_wrapped_athlete_name():
    lines = [
        "3 SUNIL PARASHARAM",
        "KONEWADKAR",
        "05-08-1993 Goa 7 65.90 "
        "250.0 250.0 260.0 260.0 [2] "
        "140.0 150.0 152.5 152.5 [2] "
        "235.0 247.5 260.0 247.5 [3] "
        "660.0 8",
    ]

    text = "\n".join(lines)

    results = parse_format2_text(text)

    assert len(results) == 1

    result = results[0]
    row = result["row"]

    assert row.athlete_name == (
        "SUNIL PARASHARAM KONEWADKAR"
    )

    assert row.place == 3
    assert row.bodyweight == 65.90

    assert row.best_squat == 260.0
    assert row.best_bench == 152.5
    assert row.best_deadlift == 247.5

    assert row.total == 660.0
    assert row.status == "PARSED"
def test_parse_format2_wrapped_athlete_name():
    text = "\n".join(
        [
            "66kg - Open",
            "3 SUNIL PARASHARAM",
            "KONEWADKAR",
            (
                "05-08-1993 Goa 7 65.90 "
                "250.0 250.0 260.0 260.0 [2] "
                "140.0 150.0 152.5 152.5 [2] "
                "235.0 247.5 260.0 247.5 [3] "
                "660.0 8"
            ),
        ]
    )

    results = parse_format2_text(text)

    assert len(results) == 1

    result = results[0]
    row = result["row"]

    assert row.place == 3

    assert row.athlete_name == (
        "SUNIL PARASHARAM KONEWADKAR"
    )

    assert row.bodyweight == 65.90

    assert row.best_squat == 260.0
    assert row.best_bench == 152.5
    assert row.best_deadlift == 247.5

    assert row.total == 660.0
    assert row.status == "PARSED"

    assert result["weight_class"] == "66"
    assert result["division"] == "Open"