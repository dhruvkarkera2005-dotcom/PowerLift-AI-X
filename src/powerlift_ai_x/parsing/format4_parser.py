from __future__ import annotations

import re
from typing import Optional

from powerlift_ai_x.parsing.result_parser import (
    ParsedRow,
    build_parsed_row,
    clean_number,
    tokenize_result_row,
)


FORMAT4_WEIGHT_CLASS_RE = re.compile(
    r"^(?P<division>.+?)\s*-\s*"
    r"(?P<weight>\d+(?:\.\d+)?|\d+\+)\s*[Kk][Gg]$"
)


def detect_format4_weight_class_section(
    line: str,
) -> Optional[tuple[str, str]]:
    normalized = " ".join(line.split())

    match = FORMAT4_WEIGHT_CLASS_RE.match(normalized)

    if not match:
        return None

    return (
        match.group("weight"),
        match.group("division").strip(),
    )


def _is_format4_header(line: str) -> bool:
    normalized = " ".join(
        line.lower().split()
    )

    return (
        normalized.startswith(
            "place name yob team"
        )
        and "coeff." in normalized
        and "sq [pl]" in normalized
        and "bp [pl]" in normalized
        and "dl [pl]" in normalized
    )


def _find_lot_bodyweight_coeff(
    tokens: list[str],
    yob_index: int,
) -> Optional[tuple[int, int, int]]:
    """
    Locate:

        Lot Bodyweight Coeff

    after YOB.

    Team names may contain multiple tokens:

        T N 14 57.20 0.168244
        M P 41 65.75 0.156198
        J & K 7 89.20 0.110883
    """

    for index in range(
        yob_index + 1,
        len(tokens) - 2,
    ):
        lot = tokens[index]

        if not re.fullmatch(r"\d+", lot):
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
    return [
        token
        for token in values
        if not (
            token.startswith("[")
            and token.endswith("]")
        )
    ]


def _parse_result_values(
    values: list[str],
) -> tuple[
    list[str],
    list[str],
    list[str],
    str,
]:
    """
    Parse the result portion of a Format 4 row.

    Normal source layout after removing [PL]:

        SQ1 SQ2 SQ3 SQ
        BP1 BP2 BP3 BP
        DL1 DL2 DL3 DL
        Total Points IPFGL BL.RK

    Therefore the normal row contains 16 values.

    Example:

        130 145 147.5 147.5
        70 80 85 85
        160 180 195 160
        392.5 12 66.035770 38

    A small number of source rows contain an additional
    value in the deadlift block:

        DL1 DL2 DL3 EXTRA DL
        Total Points IPFGL BL.RK

    Example:

        135 150 0 157.5 157.5
        377.5 9 63.631778 45

    For that anomaly we preserve the later 157.5 as
    the source-provided Best Deadlift and shift Total
    to 377.5.
    """

    # --------------------------------------------------
    # Normal Format 4 row
    # --------------------------------------------------

    if len(values) == 16:
        squat = values[0:4]
        bench = values[4:8]
        deadlift = values[8:12]
        total = values[12]

        return (
            squat,
            bench,
            deadlift,
            total,
        )

    # --------------------------------------------------
    # Format 4 deadlift-extra anomaly
    # --------------------------------------------------
    #
    # Expected length becomes 17:
    #
    # 4 SQ
    # 4 BP
    # 5 DL
    # 4 trailing
    #
    # Example:
    #
    # 135 150 0 157.5 157.5
    # 377.5 9 63.631778 45
    #
    # We interpret:
    #
    # DL1 = 135
    # DL2 = 150
    # DL3 = 0
    # Best DL = 157.5
    # Total = 377.5
    #

    if len(values) >= 17:
        squat = values[0:4]
        bench = values[4:8]

        deadlift = [
            values[8],
            values[9],
            values[10],
            values[12],
        ]

        total = values[13]

        return (
            squat,
            bench,
            deadlift,
            total,
        )

    # --------------------------------------------------
    # Incomplete / truncated row
    # --------------------------------------------------

    padded = list(values)

    while len(padded) < 16:
        padded.append("-")

    squat = padded[0:4]
    bench = padded[4:8]
    deadlift = padded[8:12]
    total = padded[12]

    return (
        squat,
        bench,
        deadlift,
        total,
    )


def parse_format4_row(
    line: str,
) -> Optional[ParsedRow]:
    """
    Parse one Format 4 row.

    Format 4 uses YOB.

    Example header:

        Place Name YOB Team Lot Bd. Wt. Coeff.
        SQ1 SQ2 SQ3 SQ [PL]
        BP1 BP2 BP3 BP [PL]
        DL1 DL2 DL3 DL [PL]
        Total Points IPF GL Points BL. RK.
    """

    line = line.strip()

    if not line:
        return None

    if _is_format4_header(line):
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
    # YOB
    # --------------------------------------------------

    yob_index: Optional[int] = None

    for index in range(
        1,
        min(len(tokens), 15),
    ):
        token = tokens[index]

        if not re.fullmatch(
            r"\d{4}",
            token,
        ):
            continue

        year = int(token)

        if 1900 <= year <= 2100:
            yob_index = index
            break

    if yob_index is None:
        return None

    # --------------------------------------------------
    # Athlete name
    # --------------------------------------------------

    athlete_name = " ".join(
        tokens[1:yob_index]
    ).strip()

    if not athlete_name:
        return None

    # --------------------------------------------------
    # Lot / Bodyweight / Coeff
    # --------------------------------------------------

    location = _find_lot_bodyweight_coeff(
        tokens,
        yob_index,
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
    # Result portion
    # --------------------------------------------------

    raw_values = tokens[
        coeff_index + 1:
    ]

    values = _remove_pl_tokens(
        raw_values
    )

    (
        squat,
        bench,
        deadlift,
        total,
    ) = _parse_result_values(values)

    # --------------------------------------------------
    # Build ParsedRow
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
        if len(squat) >= 4
        and squat[3] != "-"
        else None
    )

    row.best_bench = (
        clean_number(bench[3])
        if len(bench) >= 4
        and bench[3] != "-"
        else None
    )

    row.best_deadlift = (
        clean_number(deadlift[3])
        if len(deadlift) >= 4
        and deadlift[3] != "-"
        else None
    )

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    if row.total is None:
        row.status = "INCOMPLETE"

    return row


def parse_format4_text(
    text: str,
) -> list[dict[str, object]]:
    """
    Parse a complete Format 4 document.
    """

    results: list[dict[str, object]] = []

    current_weight_class: Optional[str] = None
    current_division: Optional[str] = None

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        section = (
            detect_format4_weight_class_section(
                line
            )
        )

        if section:
            (
                current_weight_class,
                current_division,
            ) = section

            continue

        if _is_format4_header(line):
            continue

        row = parse_format4_row(line)

        if row is None:
            continue

        results.append(
            {
                "status": row.status,
                "weight_class": current_weight_class,
                "division": current_division,
                "row": row,
                "raw_line": line,
            }
        )

    return results