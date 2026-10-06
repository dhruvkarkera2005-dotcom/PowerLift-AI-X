from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedRow:
    """Intermediate representation of one extracted result row."""

    place: Optional[int]
    athlete_name: str

    # Identity metadata preserved from the source.
    date_of_birth: Optional[str]
    team: Optional[str]
    lot: Optional[str]

    bodyweight: Optional[float]

    squat_attempt_1: Optional[float]
    squat_attempt_2: Optional[float]
    squat_attempt_3: Optional[float]
    best_squat: Optional[float]

    bench_attempt_1: Optional[float]
    bench_attempt_2: Optional[float]
    bench_attempt_3: Optional[float]
    best_bench: Optional[float]

    deadlift_attempt_1: Optional[float]
    deadlift_attempt_2: Optional[float]
    deadlift_attempt_3: Optional[float]
    best_deadlift: Optional[float]

    total: Optional[float]

    status: str = "PARSED"


def clean_number(value: str) -> Optional[float]:
    """
    Convert a result token into a numeric value.

    Examples:
        '170'     -> 170.0
        '170.5'   -> 170.5
        'X170'    -> -170.0
        '-170'    -> -170.0
        '-'       -> None
        'X'       -> None
    """

    value = value.strip()

    if not value or value == "-":
        return None

    failed = value.upper().startswith("X")

    if failed:
        value = value[1:]

    # Some PDFs use lowercase x.
    value = value.lstrip("xX")

    try:
        number = float(value)
    except ValueError:
        return None

    return -number if failed else number


def best_attempt(
    attempts: list[Optional[float]],
) -> Optional[float]:
    """
    Return the best successful attempt.

    Failed attempts are represented by negative values.
    Missing attempts are None.
    """

    successful = [
        value
        for value in attempts
        if value is not None and value >= 0
    ]

    if not successful:
        return None

    return max(successful)


def parse_place(value: str) -> Optional[int]:
    value = value.strip()

    if value.upper() == "DSQ":
        return None

    match = re.match(r"^\d+$", value)

    if not match:
        return None

    return int(value)


def parse_numeric_tokens(
    tokens: list[str],
) -> list[Optional[float]]:
    return [
        clean_number(token)
        for token in tokens
    ]


def build_parsed_row(
    *,
    place: str,
    athlete_name: str,
    date_of_birth: Optional[str] = None,
    team: Optional[str] = None,
    lot: Optional[str] = None,
    bodyweight: str,
    squat: list[str],
    bench: list[str],
    deadlift: list[str],
    total: str,
) -> ParsedRow:

    squat_values = parse_numeric_tokens(
        squat
    )

    bench_values = parse_numeric_tokens(
        bench
    )

    deadlift_values = parse_numeric_tokens(
        deadlift
    )

    return ParsedRow(
        place=parse_place(place),
        athlete_name=athlete_name.strip(),
        date_of_birth=date_of_birth,
        team=team,
        lot=lot,
        bodyweight=clean_number(bodyweight),

        squat_attempt_1=(
            squat_values[0]
            if len(squat_values) > 0
            else None
        ),
        squat_attempt_2=(
            squat_values[1]
            if len(squat_values) > 1
            else None
        ),
        squat_attempt_3=(
            squat_values[2]
            if len(squat_values) > 2
            else None
        ),
        best_squat=best_attempt(
            squat_values
        ),

        bench_attempt_1=(
            bench_values[0]
            if len(bench_values) > 0
            else None
        ),
        bench_attempt_2=(
            bench_values[1]
            if len(bench_values) > 1
            else None
        ),
        bench_attempt_3=(
            bench_values[2]
            if len(bench_values) > 2
            else None
        ),
        best_bench=best_attempt(
            bench_values
        ),

        deadlift_attempt_1=(
            deadlift_values[0]
            if len(deadlift_values) > 0
            else None
        ),
        deadlift_attempt_2=(
            deadlift_values[1]
            if len(deadlift_values) > 1
            else None
        ),
        deadlift_attempt_3=(
            deadlift_values[2]
            if len(deadlift_values) > 2
            else None
        ),
        best_deadlift=best_attempt(
            deadlift_values
        ),

        total=clean_number(total),
    )


WEIGHT_CLASS_PATTERN = re.compile(
    r"^(?P<weight>\d+(?:\.\d+)?)kg\s*-\s*(?P<division>.+)$",
    re.IGNORECASE,
)


def detect_weight_class_section(
    line: str,
) -> Optional[tuple[str, str]]:
    """
    Detect sections such as:

        59kg - Open
        66kg - Open
        74kg - Open
    """

    match = WEIGHT_CLASS_PATTERN.match(
        line.strip()
    )

    if not match:
        return None

    return (
        match.group("weight"),
        match.group("division").strip(),
    )


def is_result_row(line: str) -> bool:
    """
    Format 1 result rows start with a numeric place
    or '-' for an unranked/non-total result.
    """

    return bool(
        re.match(
            r"^(?:\d+|-)\s+\S+",
            line.strip(),
        )
    )


def tokenize_result_row(line: str) -> list[str]:
    """
    Split a Format 1 result row while preserving
    the '-' tokens used by the source.
    """

    return line.strip().split()


def parse_format1_row(
    line: str,
) -> Optional[ParsedRow]:
    """
    Parse a 2019-style Powerlifting India result row.

    Supports both complete and incomplete rows.

    Complete example:
        Place Name DOB Team Lot BW
        SQ1 SQ2 SQ3 Best [PL]
        BP1 BP2 BP3 Best [PL]
        DL1 DL2 DL3 Best [PL]
        Total Points

    Incomplete example:
        - P RAJU DOB TEL 115 73.25
        130.0 - 65.0 - 145.0 - - -
    """

    tokens = tokenize_result_row(line)

    if len(tokens) < 8:
        return None

    place = tokens[0]

    # --------------------------------------------------------
    # Find DOB
    # --------------------------------------------------------

    dob_index = None

    for index in range(
        1,
        min(len(tokens), 12),
    ):
        if re.fullmatch(
            r"\d{2}-\d{2}-\d{4}",
            tokens[index],
        ):
            dob_index = index
            break

    if dob_index is None:
        return None

    athlete_name = " ".join(
        tokens[1:dob_index]
    )

    date_of_birth = tokens[dob_index]

    if not athlete_name:
        return None

    # --------------------------------------------------------
    # Find Lot + Bodyweight
    # --------------------------------------------------------

    lot_index = None
    bodyweight_index = None

    for index in range(
        dob_index + 1,
        len(tokens) - 1,
    ):
        if not re.fullmatch(
            r"\d+",
            tokens[index],
        ):
            continue

        bodyweight_value = clean_number(
            tokens[index + 1]
        )

        if bodyweight_value is None:
            continue

        lot_index = index
        bodyweight_index = index + 1
        break

    if (
        lot_index is None
        or bodyweight_index is None
    ):
        return None

    # Everything between DOB and LOT is the team.
    team = " ".join(
        tokens[
            dob_index + 1:lot_index
        ]
    ).strip()

    lot = tokens[lot_index]

    bodyweight = clean_number(
        tokens[bodyweight_index]
    )

    values = tokens[
        bodyweight_index + 1:
    ]

    # --------------------------------------------------------
    # Remove [PL] ranking tokens
    # --------------------------------------------------------

    values = [
        token
        for token in values
        if not (
            token.startswith("[")
            and token.endswith("]")
        )
    ]

    # --------------------------------------------------------
    # Compact incomplete Format 1
    #
    # Example:
    #
    #   130.0 - 65.0 - 145.0 - - -
    # --------------------------------------------------------

    compact_incomplete = (
        len(values) >= 4
        and values[0] != "-"
        and values[1] == "-"
        and values[2] != "-"
        and values[3] == "-"
    )

    if compact_incomplete:

        squat_value = clean_number(
            values[0]
        )

        bench_value = clean_number(
            values[2]
        )

        deadlift_value = (
            clean_number(values[4])
            if len(values) > 4
            else None
        )

        row = build_parsed_row(
            place=place,
            athlete_name=athlete_name,
            date_of_birth=date_of_birth,
            team=team,
            lot=lot,
            bodyweight=(
                str(bodyweight)
                if bodyweight is not None
                else "-"
            ),
            squat=[
                (
                    str(squat_value)
                    if squat_value is not None
                    else "-"
                )
            ],
            bench=[
                (
                    str(bench_value)
                    if bench_value is not None
                    else "-"
                )
            ],
            deadlift=[
                (
                    str(deadlift_value)
                    if deadlift_value is not None
                    else "-"
                )
            ],
            total="-",
        )

        row.best_squat = squat_value
        row.best_bench = bench_value
        row.best_deadlift = deadlift_value
        row.status = "INCOMPLETE"

        return row

    # --------------------------------------------------------
    # Standard Format 1
    #
    # SQ1 SQ2 SQ3 Best
    # BP1 BP2 BP3 Best
    # DL1 DL2 DL3 Best
    # --------------------------------------------------------

    while len(values) < 14:
        values.append("-")

    squat = values[0:4]
    bench = values[4:8]
    deadlift = values[8:12]

    total = values[12]

    row = build_parsed_row(
        place=place,
        athlete_name=athlete_name,
        date_of_birth=date_of_birth,
        team=team,
        lot=lot,
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

    # --------------------------------------------------------
    # Preserve explicit source best values
    # --------------------------------------------------------

    row.best_squat = clean_number(
        squat[3]
    )

    row.best_bench = clean_number(
        bench[3]
    )

    row.best_deadlift = clean_number(
        deadlift[3]
    )

    # If a source has no explicit best value,
    # derive it only from successful attempts.

    if row.best_squat is None:
        row.best_squat = best_attempt(
            parse_numeric_tokens(
                squat[:3]
            )
        )

    if row.best_bench is None:
        row.best_bench = best_attempt(
            parse_numeric_tokens(
                bench[:3]
            )
        )

    if row.best_deadlift is None:
        row.best_deadlift = best_attempt(
            parse_numeric_tokens(
                deadlift[:3]
            )
        )

    if row.total is None:
        row.status = "INCOMPLETE"

    return row


def parse_format1_text(
    text: str,
) -> list[dict[str, object]]:
    """
    Parse all recognizable Format 1 rows.

    Returns intermediate records rather than directly
    creating CompetitionResult objects because the
    competition metadata is handled by a higher layer.
    """

    results: list[dict[str, object]] = []

    current_weight_class: Optional[str] = None
    current_division: Optional[str] = None

    for raw_line in text.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        section = detect_weight_class_section(
            line
        )

        if section:
            (
                current_weight_class,
                current_division,
            ) = section

            continue

        if not is_result_row(line):
            continue

        if (
            current_weight_class is None
            or current_division is None
        ):
            continue

        parsed = parse_format1_row(
            line
        )

        if parsed is None:
            results.append(
                {
                    "status": "REVIEW",
                    "raw_line": line,
                    "weight_class": (
                        current_weight_class
                    ),
                    "division": (
                        current_division
                    ),
                }
            )

            continue

        results.append(
            {
                "status": "PARSED",
                "weight_class": (
                    current_weight_class
                ),
                "division": (
                    current_division
                ),
                "row": parsed,
            }
        )

    return results