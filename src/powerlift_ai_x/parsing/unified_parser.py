from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from powerlift_ai_x.parsing.format_detector import detect_format
from powerlift_ai_x.parsing.result_parser import parse_format1_text
from powerlift_ai_x.parsing.format2_parser import parse_format2_text
from powerlift_ai_x.parsing.format3_parser import parse_format3_text
from powerlift_ai_x.parsing.format4_parser import parse_format4_text


@dataclass
class ParsedSource:
    source_file: str
    detected_format: str
    status: str
    results: list[dict[str, Any]]
    error: str | None = None


def parse_text(
    text: str,
    source_file: str = "",
) -> ParsedSource:
    """
    Detect and parse one extracted source document.
    """

    detected_format = detect_format(text)

    if detected_format == "FORMAT1":
        results = parse_format1_text(text)

    elif detected_format == "FORMAT2":
        results = parse_format2_text(text)

    elif detected_format == "FORMAT3":
        results = parse_format3_text(text)

    elif detected_format == "FORMAT4":
        results = parse_format4_text(text)

    else:
        return ParsedSource(
            source_file=source_file,
            detected_format="UNKNOWN",
            status="ERROR",
            results=[],
            error="Unable to detect source format.",
        )

    return ParsedSource(
        source_file=source_file,
        detected_format=detected_format,
        status="SUCCESS",
        results=results,
    )


def parse_file(
    path: str | Path,
) -> ParsedSource:
    """
    Read and parse one extracted TXT file.
    """

    path = Path(path)

    try:
        text = path.read_text(
            encoding="utf-8"
        )
    except Exception as exc:
        return ParsedSource(
            source_file=path.name,
            detected_format="UNKNOWN",
            status="ERROR",
            results=[],
            error=f"{type(exc).__name__}: {exc}",
        )

    return parse_text(
        text,
        source_file=path.name,
    )


def parse_directory(
    directory: str | Path,
) -> list[ParsedSource]:
    """
    Parse every TXT file in a directory.
    """

    directory = Path(directory)

    sources: list[ParsedSource] = []

    for path in sorted(
        directory.glob("*.txt")
    ):
        sources.append(
            parse_file(path)
        )

    return sources