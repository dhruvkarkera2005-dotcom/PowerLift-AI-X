from __future__ import annotations

import re
from typing import Optional

from powerlift_ai_x.parsing.result_parser import (
    ParsedRow,
    build_parsed_row,
    clean_number,
    tokenize_result_row,
)


FORMAT3_WEIGHT_CLASS_RE = re.compile(
    r"^(?P<division>.+?)\s*-\s*"
    r"(?P<weight>\d+(?:\.\d+)?|\d+\+)\s*[Kk][Gg]$"
)


def detect_format3_weight_class_section(
    line: str,
) -> Optional[tuple[str, str]]:
    """
    Detect modern Format 3 sections.

    Examples:

        Open - 59kg
        Open - 66kg
        Sub Junior - 74kg
        Junior - 83kg
        Senior - 93kg
    """

    normalized = " ".join(line.split())

    match = FORMAT3_WEIGHT_CLASS_RE.match(
        normalized
    )

    if not match:
        return None

    return (
        match.group("weight"),
        match.group("division").strip(),
    )


def _is_format3_header(line: str) -> bool:
    """
    Detect the modern Format 3 header.

    Example:

        Place Name DOB Team Lot Bd. Wt. Coeff.
        SQ1 SQ2 SQ3 SQ [PL]
        BP1 BP2 BP3 BP [PL]
        DL1 DL2 DL3 DL [PL]
    """

    normalized = " ".join(
        line.lower().split()
    )

    return (
        normalized.startswith(
            "place name dob team"
        )
        and "coeff." in normalized
        and "sq [pl]" in normalized
        and "bp [pl]" in normalized
        and "dl [pl]" in normalized
    )


def _is_men_section(line: str) -> bool:
    return (
        " ".join(line.lower().split())
        == "men"
    )


def _is_women_section(line: str) -> bool:
    return (
        " ".join(line.lower().split())
        == "women"
    )


def _find_lot_bodyweight_coeff(
    tokens: list[str],
    dob_index: int,
) -> Optional[tuple[int, int, int]]:
    """
    Locate:

        Lot Bodyweight Coeff

    after DOB.

    Team names can contain multiple tokens.

    Examples:

        KAR 13 58.50 0.146559
        T N 9 59.00 0.145591
        J & K 7 59.00 0.145591
    """

    for index in range(
        dob_index + 1,
        len(tokens) - 2,
    ):
        lot = tokens[index]

        if not re.fullmatch(
            r"\d+",
            lot,
        ):
            continue

        bodyweight = clean_number(
            tokens[index + 1]
        )

        coeff = clean_number(
            tokens[index + 2]
        )

        if bodyweight is None:
            continue

        if coeff is None:
            continue

        return (
            index,
            index + 1,
            index + 2,
        )

    return None


def _remove_pl_tokens(
    values: list[str],
) -> list[str]:
    """
    Remove [PL] placement tokens while preserving
    actual lift values, X and -.
    """

    return [
        token
        for token in values
        if not (
            token.startswith("[")
            and token.endswith("]")
        )
    ]


def parse_format3_row(
    line: str,
) -> Optional[ParsedRow]:
    """
    Parse one modern Format 3 result row.

    Format:

        Place Name DOB Team Lot Bd.Wt. Coeff.
        SQ1 SQ2 SQ3 SQ [PL]
        BP1 BP2 BP3 BP [PL]
        DL1 DL2 DL3 DL [PL]
        Total Points IPF GL Points Place

    Format 3 uses the fourth lift value as the
    source-provided Best value.
    """

    line = line.strip()

    if not line:
        return None

    if _is_format3_header(line):
        return None

    if _is_men_section(line):
        return None

    if _is_women_section(line):
        return None

    tokens = tokenize_result_row(line)

    if len(tokens) < 10:
        return None

    # --------------------------------------------------
    # Place
    # --------------------------------------------------

    place_token = tokens[0]

    if place_token != "-":
        if not re.fullmatch(
            r"\d+",
            place_token,
        ):
            return None

    # --------------------------------------------------
    # DOB
    # --------------------------------------------------

    dob_index: Optional[int] = None

    for index in range(
        1,
        min(len(tokens), 15),
    ):
        if re.fullmatch(
            r"\d{2}-\d{2}-\d{4}",
            tokens[index],
        ):
            dob_index = index
            break

    if dob_index is None:
        return None

    # --------------------------------------------------
    # Athlete name
    # --------------------------------------------------

    athlete_name = " ".join(
        tokens[1:dob_index]
    ).strip()

    if not athlete_name:
        return None

    # --------------------------------------------------
    # Lot / Bodyweight / Coeff
    # --------------------------------------------------

    location = _find_lot_bodyweight_coeff(
        tokens,
        dob_index,
    )

    if location is None:
        return None

    (
        _lot_index,
        bodyweight_index,
        coeff_index,
    ) = location

    bodyweight = clean_number(
        tokens[bodyweight_index]
    )

    # --------------------------------------------------
    # Lift/result values
    # --------------------------------------------------

    values = tokens[
        coeff_index + 1:
    ]

    values = _remove_pl_tokens(
        values
    )

    # After removing [PL]:

    # SQ1 SQ2 SQ3 SQ
    # BP1 BP2 BP3 BP
    # DL1 DL2 DL3 DL
    # Total Points IPFGL Place

    while len(values) < 15:
        values.append("-")

    squat = values[0:4]
    bench = values[4:8]
    deadlift = values[8:12]

    total = values[12]

    # --------------------------------------------------
    # Build common ParsedRow
    # --------------------------------------------------

    row = build_parsed_row(
        place=place_token,
        athlete_name=athlete_name,
        bodyweight=(
            str(bodyweight)
            if bodyweight is not None
            else "-"
        ),
        squat=squat[:3],
        bench=bench[:3],
        deadlift=deadlift[:3],
        total=total,
    )

    # --------------------------------------------------
    # Source-provided Best values
    # --------------------------------------------------

    row.best_squat = (
        clean_number(squat[3])
        if squat[3] != "-"
        else None
    )

    row.best_bench = (
        clean_number(bench[3])
        if bench[3] != "-"
        else None
    )

    row.best_deadlift = (
        clean_number(deadlift[3])
        if deadlift[3] != "-"
        else None
    )

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    if row.total is None:
        row.status = "INCOMPLETE"

    return row


def parse_format3_text(
    text: str,
) -> list[dict[str, object]]:
    """
    Parse an entire Format 3 document.

    Supports:

        Men
        Open - 59kg

        Women
        Open - 59kg

    and documents without explicit gender sections.

    Summary tables such as:

        Best Lifter - Sub Junior
        Team Championship - Sub Junior

    are excluded from the canonical individual
    competition-result records.
    """

    results: list[dict[str, object]] = []

    # --------------------------------------------------
    # Determine whether the document explicitly contains
    # gender sections.
    # --------------------------------------------------

    has_men_section = any(
        _is_men_section(line)
        for line in text.splitlines()
    )

    has_women_section = any(
        _is_women_section(line)
        for line in text.splitlines()
    )

    has_explicit_gender_sections = (
        has_men_section or has_women_section
    )

    # --------------------------------------------------
    # Default gender
    # --------------------------------------------------

    current_gender: Optional[str] = (
        None
        if has_explicit_gender_sections
        else "Men"
    )

    current_weight_class: Optional[str] = None
    current_division: Optional[str] = None

    # True while processing summary tables such as
    # Best Lifter and Team Championship.
    in_summary_section = False

    # --------------------------------------------------
    # Process document line-by-line
    # --------------------------------------------------

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        # --------------------------------------------------
        # Gender section
        # --------------------------------------------------

        if _is_men_section(line):
            current_gender = "Men"
            in_summary_section = False
            continue

        if _is_women_section(line):
            current_gender = "Women"
            in_summary_section = False
            continue

        # --------------------------------------------------
        # Summary sections
        #
        # These are NOT individual competition-result
        # tables and must not be parsed as ParsedRow.
        # --------------------------------------------------

        normalized_line = " ".join(
            line.lower().split()
        )

        if normalized_line.startswith(
            "best lifter -"
        ):
            in_summary_section = True
            continue

        if normalized_line.startswith(
            "team championship -"
        ):
            in_summary_section = True
            continue

        # --------------------------------------------------
        # Weight-class section
        #
        # A new weight-class section ends a previous
        # summary section.
        # --------------------------------------------------

        section = detect_format3_weight_class_section(
            line
        )

        if section:
            (
                current_weight_class,
                current_division,
            ) = section

            in_summary_section = False

            continue

        # --------------------------------------------------
        # Header
        # --------------------------------------------------

        if _is_format3_header(line):
            continue

        # --------------------------------------------------
        # Only Men's results
        # --------------------------------------------------

        if current_gender != "Men":
            continue

        # --------------------------------------------------
        # Ignore summary tables
        # --------------------------------------------------

        if in_summary_section:
            continue

        # --------------------------------------------------
        # Result row
        # --------------------------------------------------

        row = parse_format3_row(line)

        if row is None:
            continue

        results.append(
            {
                "status": row.status,
                "weight_class": current_weight_class,
                "division": current_division,
                "gender": current_gender,
                "row": row,
                "raw_line": line,
            }
        )

    return results