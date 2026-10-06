from pathlib import Path

from powerlift_ai_x.parsing.format_detector import (
    detect_format,
)


def read_extracted(name: str) -> str:
    return Path(
        "data/extracted"
    ).joinpath(name).read_text(
        encoding="utf-8",
        errors="replace",
    )


def test_detect_format1_real_file():
    text = read_extracted(
        "20190930045738ab.txt"
    )

    assert detect_format(text) == "FORMAT1"


def test_detect_format2_real_file():
    text = read_extracted(
        "20220610033709ab.txt"
    )

    assert detect_format(text) == "FORMAT2"


def test_detect_format3_real_file():
    text = read_extracted(
        "20241124011317ab.txt"
    )

    assert detect_format(text) == "FORMAT3"


def test_detect_format4_real_file():
    text = read_extracted(
        "_National_Masters_Classic_Powerlifting_Championship_2026_M_024535.txt"
    )

    assert detect_format(text) == "FORMAT4"