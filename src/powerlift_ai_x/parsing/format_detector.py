from __future__ import annotations

import re


def _normalized(text: str) -> str:
    return " ".join(text.lower().split())


def _has_weight_class_section(text: str) -> bool:
    """
    Detect common Powerlifting India weight-class sections.

    Examples:

        59kg - Open
        66kg - Master 1
        Open - 59kg
        Sub Junior - 53kg
        Master 1 - 59kg
    """

    patterns = [
        r"\b\d+(?:\.\d+)?\s*\+\s*kg\s*-\s*.+",
        r"\b\d+(?:\.\d+)?\s*kg\s*-\s*.+",
        r"\b.+?\s*-\s*\d+(?:\.\d+)?\s*\+\s*kg\b",
        r"\b.+?\s*-\s*\d+(?:\.\d+)?\s*kg\b",
    ]

    return any(
        re.search(
            pattern,
            text,
            re.IGNORECASE,
        )
        for pattern in patterns
    )


def _has_result_header(text: str) -> bool:
    """
    Detect the common legacy result-table header.

    Example:

        Place Name DOB Team Lot Bd. Wt. Coeff.
        SQ1 SQ2 SQ3 Best [PL]
        BP1 BP2 BP3 Best [PL]
        DL1 DL2 DL3 Best [PL]
    """

    normalized = _normalized(text)

    return (
        "place name dob team" in normalized
        and "sq1" in normalized
        and "bp1" in normalized
        and "dl1" in normalized
    )


def _has_modern_lifts(text: str) -> bool:
    """
    Detect the modern lift layout.

    Example:

        SQ [PL]
        BP [PL]
        DL [PL]
    """

    normalized = _normalized(text)

    return (
        "sq [pl]" in normalized
        and "bp [pl]" in normalized
        and "dl [pl]" in normalized
    )


def _has_ipf_gl_points(text: str) -> bool:
    """
    Detect the IPF GL Points column.
    """

    normalized = _normalized(text)

    return "ipf gl points" in normalized


def _has_wrapped_result_row(text: str) -> bool:
    """
    Detect PDF extraction where an athlete result row is
    physically wrapped across multiple lines.

    Example:

        3 SUNIL PARASHARAM
        KONEWADKAR
        05-08-1993 Goa 7 65.90 ...

    The first line begins like a result row but does not
    contain the DOB. A following line contains the DOB.

    This is a structural detector and does not depend on
    any particular athlete, competition, federation, or year.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    date_pattern = re.compile(
        r"\b\d{2}[-/]\d{2}[-/]\d{4}\b"
    )

    result_start_pattern = re.compile(
        r"^(?:\d+|-)\s+\S+"
    )

    for index, line in enumerate(lines):

        if not result_start_pattern.match(line):
            continue

        # A normal complete row already contains its DOB.
        if date_pattern.search(line):
            continue

        # Look ahead for a wrapped continuation containing DOB.
        for next_index in range(
            index + 1,
            min(index + 5, len(lines)),
        ):
            next_line = lines[next_index]

            if date_pattern.search(next_line):
                return True

            # Another result row means this was not wrapped.
            if result_start_pattern.match(next_line):
                break

            # A new weight-class section means this was not wrapped.
            if re.search(
                r"\b\d+(?:\.\d+)?\s*kg\s*-",
                next_line,
                re.IGNORECASE,
            ):
                break

    return False


def detect_format(text: str) -> str:
    """
    Detect the structural format of an extracted
    Powerlifting India result document.

    Returns:

        FORMAT1
        FORMAT2
        FORMAT3
        FORMAT4
        UNKNOWN
    """

    normalized = _normalized(text)

    has_weight_class = _has_weight_class_section(
        normalized
    )

    has_coeff = "coeff." in normalized

    # ==================================================
    # FORMAT 4
    #
    # Masters/YOB layout.
    #
    # Place Name YOB Team ...
    # ==================================================

    has_yob = bool(
        re.search(
            r"\bplace\s+name\s+yob\s+team\b",
            normalized,
        )
    )

    if (
        has_yob
        and has_coeff
        and has_weight_class
    ):
        return "FORMAT4"

    # ==================================================
    # FORMAT 3
    #
    # Modern layout:
    #
    # SQ [PL]
    # BP [PL]
    # DL [PL]
    #
    # with IPF GL Points.
    # ==================================================

    has_dob = bool(
        re.search(
            r"\bplace\s+name\s+dob\s+team\b",
            normalized,
        )
    )

    has_modern_lifts = _has_modern_lifts(
        normalized
    )

    has_ipf_gl = _has_ipf_gl_points(
        normalized
    )

    if (
        has_dob
        and has_coeff
        and has_modern_lifts
        and has_ipf_gl
        and has_weight_class
    ):
        return "FORMAT3"

    # ==================================================
    # FORMAT 2 / FORMAT 1
    #
    # Both can use the legacy:
    #
    # SQ1 SQ2 SQ3 Best [PL]
    # BP1 BP2 BP3 Best [PL]
    # DL1 DL2 DL3 Best [PL]
    #
    # Therefore SQ1/BP1/DL1 alone cannot distinguish
    # Format 1 from Format 2.
    #
    # Format 2 signatures:
    #
    #   1. Coeff. exists
    #   2. OR the PDF contains wrapped result rows
    #
    # Format 1:
    #
    #   legacy layout without those Format 2 signatures.
    # ==================================================

    has_legacy_header = _has_result_header(
        normalized
    )

    has_wrapped_rows = _has_wrapped_result_row(
        text
    )

    # --------------------------------------------------
    # FORMAT 2
    # --------------------------------------------------

    if (
        has_dob
        and has_legacy_header
        and has_weight_class
        and (
            has_coeff
            or has_wrapped_rows
        )
    ):
        return "FORMAT2"

    # --------------------------------------------------
    # FORMAT 1
    # --------------------------------------------------

    has_format1_header = (
        "place name dob team" in normalized
        and "sq1" in normalized
        and "bp1" in normalized
        and "dl1" in normalized
        and "total points" in normalized
    )

    if (
        has_format1_header
        and not has_coeff
        and not has_wrapped_rows
    ):
        return "FORMAT1"

    return "UNKNOWN"