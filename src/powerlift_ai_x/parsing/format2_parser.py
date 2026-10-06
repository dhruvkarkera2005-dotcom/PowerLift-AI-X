from __future__ import annotations

import re
from typing import Optional

from powerlift_ai_x.parsing.result_parser import (
    ParsedRow,
    clean_number,
)


# ============================================================
# WEIGHT-CLASS SECTION
# ============================================================

WEIGHT_CLASS_RE = re.compile(
    r"^(?P<weight>\d+(?:\.\d+)?|\d+\+)\s*[Kk][Gg]\s*-\s*"
    r"(?P<division>.+)$"
)


def detect_format2_weight_class_section(
    line: str,
) -> Optional[tuple[str, str]]:
    """
    Detect a Format 2 weight-class section.

    Supported forms:

        59kg - Open
        66kg - Open
        74kg - Junior
        120+Kg - Open

    Also supports:

        Open - 59kg
        Junior - 83kg
        Sub Junior - 120+Kg
    """

    normalized = " ".join(
        line.split()
    )

    # --------------------------------------------------------
    # Standard:
    #
    #     59kg - Open
    # --------------------------------------------------------

    match = WEIGHT_CLASS_RE.match(
        normalized
    )

    if match:
        return (
            match.group("weight"),
            match.group("division").strip(),
        )

    # --------------------------------------------------------
    # Division first:
    #
    #     Open - 59kg
    # --------------------------------------------------------

    division_first_match = re.match(
        r"^(?P<division>.+?)\s*-\s*"
        r"(?P<weight>\d+(?:\.\d+)?|\d+\+)\s*[Kk][Gg]$",
        normalized,
        re.IGNORECASE,
    )

    if division_first_match:
        return (
            division_first_match.group("weight"),
            division_first_match.group("division").strip(),
        )

    return None


# ============================================================
# INLINE WEIGHT CLASS
# ============================================================

INLINE_WEIGHT_CLASS_RE = re.compile(
    r"^(?P<weight>\d+(?:\.\d+)?|\d+\+)\s*[Kk][Gg]$",
    re.IGNORECASE,
)


def detect_format2_inline_weight_class(
    tokens: list[str],
) -> Optional[tuple[int, str]]:
    """
    Detect an inline weight-class token.

    Examples:

        1 SURESH P J&K 59kg 59.00 ...
        2 C ARIVALAGAN RSPB 93kg 92.20 ...
        3 ATHLETE MAH 59kg ...

    Returns:

        (token_index, weight_class)

    or:

        None
    """

    for index, token in enumerate(tokens):

        match = INLINE_WEIGHT_CLASS_RE.match(
            token.strip()
        )

        if match:
            return (
                index,
                match.group("weight"),
            )

    return None


# ============================================================
# HEADER DETECTION
# ============================================================

def _is_format2_header(
    line: str,
) -> bool:
    """
    Detect repeated Format 2 column headers.
    """

    normalized = " ".join(
        line.lower().split()
    )

    return (
        normalized.startswith(
            "place name dob team"
        )
        and "coeff" in normalized
        and "ipf gl points" in normalized
    )


# ============================================================
# SUMMARY SECTION DETECTION
# ============================================================

def _is_summary_header(
    line: str,
) -> bool:
    """
    Detect summary sections that must not be parsed
    as individual competition-result rows.
    """

    normalized = " ".join(
        line.lower().split()
    )

    return (
        normalized.startswith(
            "best lifter -"
        )
        or normalized.startswith(
            "team championship -"
        )
    )


def _is_summary_column_header(
    line: str,
) -> bool:
    """
    Detect headers belonging to summary tables.
    """

    normalized = " ".join(
        line.lower().split()
    )

    return (
        normalized.startswith(
            "place name team"
        )
        or normalized.startswith(
            "place team points"
        )
        or normalized.startswith(
            "place name team wt.cat."
        )
    )


# ============================================================
# RESULT ROW HELPERS
# ============================================================

DATE_RE = re.compile(
    r"^\d{2}-\d{2}-\d{4}$"
)


def _find_date_index(
    tokens: list[str],
) -> Optional[int]:
    """
    Find the DOB token.

    DOB is used as the stable boundary between
    athlete name and metadata.
    """

    for index, token in enumerate(tokens):

        if DATE_RE.match(token):
            return index

    return None


def _is_failed_attempt(
    token: str,
) -> bool:
    """
    Recognize failed or missing attempts.
    """

    return token.upper() in {
        "X",
        "FAIL",
        "-",
    }


def _clean_attempt(
    token: str,
) -> Optional[float]:
    """
    Convert one attempt token into a numeric value.

    Failed/missing attempts become None.
    """

    if _is_failed_attempt(token):
        return None

    return clean_number(token)


# ============================================================
# FORMAT 2 RESULT ROW
# ============================================================

def parse_format2_row(
    line: str,
) -> Optional[ParsedRow]:
    """
    Parse one Format 2 result row.

    Format:

        PLACE NAME DOB TEAM LOT BODYWEIGHT COEFF
        S1 S2 S3 BEST [PLACE]
        B1 B2 B3 BEST [PLACE]
        D1 D2 D3 BEST [PLACE]
        TOTAL ...

    Format 2 explicitly supplies BEST as the fourth
    value of each lift group.
    """

    tokens = line.split()

    if len(tokens) < 10:
        return None

    # --------------------------------------------------------
    # Place
    # --------------------------------------------------------

    place_token = tokens[0]

    if place_token == "-":
        place = None

    elif place_token.isdigit():
        place = int(place_token)

    else:
        return None

    # --------------------------------------------------------
    # DOB
    # --------------------------------------------------------

    dob_index = _find_date_index(
        tokens
    )

    if dob_index is None:
        return None

    if dob_index <= 1:
        return None

    # --------------------------------------------------------
    # Athlete name
    # --------------------------------------------------------

    athlete_name = " ".join(
        tokens[1:dob_index]
    ).strip()
    date_of_birth = tokens[dob_index]

    if not athlete_name:
        return None

    # --------------------------------------------------------
    # Find LOT / BODYWEIGHT / optional COEFF
    # --------------------------------------------------------

    metadata_start = dob_index + 1

    lot_index: Optional[int] = None
    bodyweight_index: Optional[int] = None
    coeff_index: Optional[int] = None

    for index in range(
        metadata_start,
        min(
            len(tokens) - 1,
            metadata_start + 12,
        ),
    ):

        if not tokens[index].isdigit():
            continue

        try:
            candidate_bodyweight = float(
                tokens[index + 1]
            )
        except ValueError:
            continue

        if candidate_bodyweight <= 0:
            continue

        lot_index = index
        bodyweight_index = index + 1

        coeff_candidate_index = index + 2

        if coeff_candidate_index < len(tokens):

            try:
                coeff_candidate = float(
                    tokens[
                        coeff_candidate_index
                    ]
                )

            except ValueError:
                coeff_candidate = None

            if (
                coeff_candidate is not None
                and 0 < coeff_candidate < 2.0
            ):
                coeff_index = (
                    coeff_candidate_index
                )

        break

    if (
        lot_index is None
        or bodyweight_index is None
    ):
        return None
    team = " ".join(
        tokens[dob_index + 1:lot_index]
        ).strip()
    lot = tokens[lot_index]

    bodyweight = clean_number(
        tokens[bodyweight_index]
    )

    # --------------------------------------------------------
    # Performance starts after metadata
    # --------------------------------------------------------

    if coeff_index is not None:
        performance_start = (
            coeff_index + 1
        )
    else:
        performance_start = (
            bodyweight_index + 1
        )

    performance = tokens[
        performance_start:
    ]

    if len(performance) < 12:
        return None

    # --------------------------------------------------------
    # Lift group reader
    # --------------------------------------------------------

    def read_lift_group(
        start: int,
    ) -> tuple[list[str], int]:

        if start + 4 > len(
            performance
        ):
            raise ValueError(
                "Incomplete lift group"
            )

        group = performance[
            start:start + 4
        ]

        next_index = start + 4

        if (
            next_index < len(performance)
            and re.fullmatch(
                r"\[\d+\]",
                performance[next_index],
            )
        ):
            next_index += 1

        return group, next_index

    # --------------------------------------------------------
    # Parse lifts
    # --------------------------------------------------------

    try:

        squat, index = (
            read_lift_group(0)
        )

        bench, index = (
            read_lift_group(index)
        )

        deadlift, index = (
            read_lift_group(index)
        )

    except ValueError:
        return None

    # --------------------------------------------------------
    # Total
    # --------------------------------------------------------

    total = None

    if index < len(performance):

        total_token = performance[
            index
        ]

        if total_token.upper() not in {
            "-",
            "X",
            "XX",
            "TD",
            "DQ",
            "DSQ",
        }:

            total = clean_number(
                total_token
            )

    # --------------------------------------------------------
    # Attempts
    # --------------------------------------------------------

    squat_attempt_1 = _clean_attempt(
        squat[0]
    )

    squat_attempt_2 = _clean_attempt(
        squat[1]
    )

    squat_attempt_3 = _clean_attempt(
        squat[2]
    )

    bench_attempt_1 = _clean_attempt(
        bench[0]
    )

    bench_attempt_2 = _clean_attempt(
        bench[1]
    )

    bench_attempt_3 = _clean_attempt(
        bench[2]
    )

    deadlift_attempt_1 = _clean_attempt(
        deadlift[0]
    )

    deadlift_attempt_2 = _clean_attempt(
        deadlift[1]
    )

    deadlift_attempt_3 = _clean_attempt(
        deadlift[2]
    )

    # --------------------------------------------------------
    # Source-provided BEST
    # --------------------------------------------------------

    def parse_source_best(
        token: str,
    ) -> Optional[float]:

        if token.upper() in {
            "-",
            "X",
            "XX",
            "TD",
            "DQ",
            "DSQ",
        }:
            return None

        return clean_number(
            token
        )

    best_squat = parse_source_best(
        squat[3]
    )

    best_bench = parse_source_best(
        bench[3]
    )

    best_deadlift = parse_source_best(
        deadlift[3]
    )

    # --------------------------------------------------------
    # Construct ParsedRow directly.
    # --------------------------------------------------------

    return ParsedRow(
    place=place,
    athlete_name=athlete_name,
    date_of_birth=date_of_birth,
    team=team,
    lot=lot,
    bodyweight=bodyweight,

        squat_attempt_1=squat_attempt_1,
        squat_attempt_2=squat_attempt_2,
        squat_attempt_3=squat_attempt_3,
        best_squat=best_squat,

        bench_attempt_1=bench_attempt_1,
        bench_attempt_2=bench_attempt_2,
        bench_attempt_3=bench_attempt_3,
        best_bench=best_bench,

        deadlift_attempt_1=deadlift_attempt_1,
        deadlift_attempt_2=deadlift_attempt_2,
        deadlift_attempt_3=deadlift_attempt_3,
        best_deadlift=best_deadlift,

        total=total,

        status=(
            "PARSED"
            if total is not None
            else "INCOMPLETE"
        ),
    )


# ============================================================
# WRAPPED RESULT ROW HANDLING
# ============================================================

def _looks_like_format2_result_start(
    line: str,
) -> bool:
    """
    Return True when a line begins like a Format 2
    result row.
    """

    tokens = line.split()

    if len(tokens) < 2:
        return False

    place = tokens[0]

    return (
        place == "-"
        or place.isdigit()
    )


def _join_wrapped_format2_rows(
    lines: list[str],
) -> list[str]:
    """
    Join PDF-extracted physical lines belonging
    to one logical Format 2 result row.

    IMPORTANT:

    A wrapped athlete name may look like:

        3 SUNIL PARASHARAM
        KONEWADKAR
        05-08-1993 Goa ...

    This becomes:

        3 SUNIL PARASHARAM KONEWADKAR
        05-08-1993 Goa ...

    The weight-class section itself is never
    merged into an athlete row.
    """

    joined: list[str] = []

    current: Optional[str] = None

    for raw_line in lines:

        line = " ".join(
            raw_line.split()
        )

        if not line:
            continue

        # ----------------------------------------------------
        # A new result row starts.
        # ----------------------------------------------------

        if _looks_like_format2_result_start(
            line
        ):

            if current is not None:
                joined.append(
                    current
                )

            current = line
            continue

        # ----------------------------------------------------
        # Weight-class headers must NEVER be joined
        # to the previous athlete.
        # ----------------------------------------------------

        if (
            detect_format2_weight_class_section(
                line
            )
            is not None
        ):

            if current is not None:
                joined.append(
                    current
                )
                current = None

            joined.append(line)
            continue

        # ----------------------------------------------------
        # Normal continuation of wrapped row.
        # ----------------------------------------------------

        if current is not None:

            candidate = (
                f"{current} {line}"
            )

            candidate_tokens = (
                candidate.split()
            )

            if (
                _find_date_index(
                    candidate_tokens
                )
                is not None
            ):

                joined.append(
                    candidate
                )

                current = None

            else:
                current = candidate

            continue

        # ----------------------------------------------------
        # Standalone non-row line.
        # ----------------------------------------------------

        joined.append(line)

    if current is not None:
        joined.append(current)

    return joined


# ============================================================
# FULL FORMAT 2 TEXT PARSER
# ============================================================

def parse_format2_text(
    text: str,
) -> list[dict[str, object]]:
    """
    Parse an entire Format 2 document.

    Supports:

        59kg - Open

        Open - 59kg

    and inline weight classes.

    Wrapped athlete rows are joined before parsing.
    """

    results: list[
        dict[str, object]
    ] = []

    current_weight_class: Optional[
        str
    ] = None

    current_division: Optional[
        str
    ] = None

    in_summary_section = False

    # --------------------------------------------------------
    # Join wrapped PDF lines.
    # --------------------------------------------------------

    lines = _join_wrapped_format2_rows(
        text.splitlines()
    )

    # --------------------------------------------------------
    # Process logical lines.
    # --------------------------------------------------------

    for raw_line in lines:

        line = " ".join(
            raw_line.split()
        )

        if not line:
            continue

        # ----------------------------------------------------
        # Headers
        # ----------------------------------------------------

        if _is_format2_header(
            line
        ):
            continue

        if _is_summary_header(
            line
        ):

            in_summary_section = True
            continue

        if _is_summary_column_header(
            line
        ):
            continue

        # ----------------------------------------------------
        # Weight-class section
        # ----------------------------------------------------

        section = (
            detect_format2_weight_class_section(
                line
            )
        )

        if section is not None:

            (
                current_weight_class,
                current_division,
            ) = section

            in_summary_section = False

            continue

        # ----------------------------------------------------
        # Ignore summary tables.
        # ----------------------------------------------------

        if in_summary_section:
            continue

        # ----------------------------------------------------
        # Parse result.
        # ----------------------------------------------------

        row = parse_format2_row(
            line
        )

        if row is None:
            continue

        # ----------------------------------------------------
        # Weight class.
        #
        # Prefer an explicit inline weight class
        # if the row contains one.
        #
        # Otherwise use the current section.
        # ----------------------------------------------------

        tokens = line.split()

        inline_weight = (
            detect_format2_inline_weight_class(
                tokens
            )
        )

        if inline_weight is not None:

            _, row_weight_class = (
                inline_weight
            )

            weight_class = (
                row_weight_class
            )

        else:

            weight_class = (
                current_weight_class
            )

        # ----------------------------------------------------
        # Store parsed result.
        # ----------------------------------------------------

        results.append(
            {
                "status": row.status,
                "weight_class": weight_class,
                "division": current_division,
                "row": row,
                "raw_line": line,
            }
        )

    return results