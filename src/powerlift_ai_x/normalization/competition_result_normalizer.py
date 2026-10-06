from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional

from powerlift_ai_x.models.competition_result import (
    CompetitionResult,
)
from powerlift_ai_x.models.enums import Equipment
from powerlift_ai_x.parsing.result_parser import ParsedRow
from powerlift_ai_x.parsing.unified_parser import (
    ParsedSource,
    parse_directory,
)


# ============================================================
# ATHLETE NAME
# ============================================================

def normalize_athlete_name(name: str) -> str:
    """
    Normalize an athlete name for canonical storage and
    deterministic athlete ID generation.
    """

    return " ".join(
        name.strip().split()
    ).upper()


def make_athlete_id(name: str) -> str:
    """
    Generate a deterministic identifier from the normalized
    athlete name.
    """

    normalized = normalize_athlete_name(
        name
    )

    digest = hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()[:16]

    return f"ATH-{digest}"


# ============================================================
# YEAR
# ============================================================

def parse_year(value: Any) -> int:
    """
    Convert manifest year metadata into an integer.
    """

    if isinstance(value, int):
        return value

    if isinstance(value, str):

        match = re.search(
            r"\b(?:19|20)\d{2}\b",
            value,
        )

        if match:
            return int(
                match.group(0)
            )

    raise ValueError(
        f"Unable to determine year from: {value!r}"
    )


# ============================================================
# EQUIPMENT
# ============================================================

def infer_equipment(
    competition: str,
) -> Equipment:
    """
    Infer equipment from the competition name.

    Explicitly identified Classic competitions are CLASSIC.
    Explicitly identified Equipped competitions are EQUIPPED.
    Everything else remains UNKNOWN.
    """

    value = competition.strip().lower()

    if "equipped" in value:
        return Equipment.EQUIPPED

    if "classic" in value:
        return Equipment.CLASSIC

    return Equipment.UNKNOWN


# ============================================================
# NUMERIC VALUES
# ============================================================

def normalize_lift_value(
    value: Optional[float],
) -> Optional[float]:
    """
    Preserve the parser's numeric representation.

    Positive values are successful lifts.

    Negative values represent failed attempts and are
    intentionally preserved.

    None represents missing data.
    """

    if value is None:
        return None

    return float(value)


# ============================================================
# SINGLE RESULT
# ============================================================

def normalize_result(
    *,
    row: ParsedRow,
    competition: str,
    year: int,
    division: str,
    weight_class: str,
    equipment: Equipment,
) -> CompetitionResult:
    """
    Convert one ParsedRow into the canonical
    CompetitionResult model.
    """

    athlete_name = normalize_athlete_name(
        row.athlete_name
    )

    return CompetitionResult(
        athlete_id=make_athlete_id(
            athlete_name
        ),
        athlete_name=athlete_name,

        competition=competition.strip(),

        year=parse_year(year),

        division=division.strip(),

        weight_class=str(
            weight_class
        ).strip(),

        equipment=equipment,

date_of_birth=row.date_of_birth,

team=(
    row.team.strip()
    if row.team
    else None
),

lot=(
    row.lot.strip()
    if row.lot
    else None
),

bodyweight=normalize_lift_value(
    row.bodyweight
),

        squat_1=normalize_lift_value(
            row.squat_attempt_1
        ),

        squat_2=normalize_lift_value(
            row.squat_attempt_2
        ),

        squat_3=normalize_lift_value(
            row.squat_attempt_3
        ),

        best_squat=normalize_lift_value(
            row.best_squat
        ),

        bench_1=normalize_lift_value(
            row.bench_attempt_1
        ),

        bench_2=normalize_lift_value(
            row.bench_attempt_2
        ),

        bench_3=normalize_lift_value(
            row.bench_attempt_3
        ),

        best_bench=normalize_lift_value(
            row.best_bench
        ),

        deadlift_1=normalize_lift_value(
            row.deadlift_attempt_1
        ),

        deadlift_2=normalize_lift_value(
            row.deadlift_attempt_2
        ),

        deadlift_3=normalize_lift_value(
            row.deadlift_attempt_3
        ),

        best_deadlift=normalize_lift_value(
            row.best_deadlift
        ),

        total=normalize_lift_value(
            row.total
        ),

        place=row.place,
    )


# ============================================================
# MANIFEST
# ============================================================

def load_source_manifest(
    path: str | Path,
) -> dict[str, dict[str, Any]]:
    """
    Load final_source_manifest.json.

    The manifest is indexed by PDF filename.
    """

    path = Path(path)

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(data, list):
        raise ValueError(
            "Source manifest must contain a JSON list."
        )

    manifest: dict[
        str,
        dict[str, Any],
    ] = {}

    for item in data:

        if not isinstance(
            item,
            dict,
        ):
            continue

        filename = item.get(
            "filename"
        )

        if not filename:
            continue

        filename = Path(
            str(filename)
        ).name

        manifest[
            filename.lower()
        ] = item

    return manifest


# ============================================================
# EXTRACTED TXT → SOURCE MANIFEST
# ============================================================

def find_source_metadata(
    source_file: str,
    manifest: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Match an extracted TXT file to its source PDF.

    Example:

        20190930045738ab.txt
                ↓
        20190930045738ab.pdf

    This avoids relying on manifest ordering.
    """

    source_name = Path(
        source_file
    ).name

    source_stem = Path(
        source_name
    ).stem

    pdf_name = (
        f"{source_stem}.pdf"
    )

    metadata = manifest.get(
        pdf_name.lower()
    )

    if metadata is not None:
        return metadata

    # --------------------------------------------------------
    # Fallback: compare manifest local_path stems.
    # --------------------------------------------------------

    for item in manifest.values():

        filename = item.get(
            "filename"
        )

        local_path = item.get(
            "local_path"
        )

        candidates = []

        if filename:
            candidates.append(
                Path(
                    str(filename)
                ).stem
            )

        if local_path:
            candidates.append(
                Path(
                    str(local_path)
                ).stem
            )

        for candidate in candidates:

            if candidate.lower() == (
                source_stem.lower()
            ):
                return item

    raise ValueError(
        "No manifest entry found for "
        f"extracted source {source_name!r}. "
        f"Expected source PDF {pdf_name!r}."
    )


# ============================================================
# ONE PARSED SOURCE
# ============================================================

def normalize_source(
    source: ParsedSource,
    metadata: dict[str, Any],
) -> list[CompetitionResult]:
    """
    Normalize all PARSED rows from one source.

    INCOMPLETE and REVIEW records remain outside the canonical
    complete-result dataset.
    """

    competition = metadata.get(
        "competition"
    )

    year = metadata.get(
        "year"
    )

    if not competition:
        raise ValueError(
            "Missing competition metadata for "
            f"{source.source_file}"
        )

    if year is None:
        raise ValueError(
            "Missing year metadata for "
            f"{source.source_file}"
        )

    equipment = infer_equipment(
        str(competition)
    )

    normalized: list[
        CompetitionResult
    ] = []

    for result in source.results:

        if result.get(
            "status"
        ) != "PARSED":
            continue

        row = result.get(
            "row"
        )

        if not isinstance(
            row,
            ParsedRow,
        ):
            continue

        weight_class = result.get(
            "weight_class"
        )

        division = result.get(
            "division"
        )

        if weight_class is None:
            raise ValueError(
                "Missing weight class in "
                f"{source.source_file}"
            )

        if division is None:
            raise ValueError(
                "Missing division in "
                f"{source.source_file}"
            )

        normalized.append(
            normalize_result(
                row=row,
                competition=str(
                    competition
                ),
                year=parse_year(
                    year
                ),
                division=str(
                    division
                ),
                weight_class=str(
                    weight_class
                ),
                equipment=equipment,
            )
        )

    return normalized


# ============================================================
# DIRECTORY
# ============================================================

def normalize_directory(
    extracted_directory: str | Path,
    manifest_path: str | Path,
) -> list[CompetitionResult]:
    """
    Parse every extracted TXT source and normalize every
    successfully parsed result into CompetitionResult.

    INCOMPLETE and REVIEW rows are excluded from the canonical
    complete-result dataset.
    """

    sources = parse_directory(
        extracted_directory
    )

    manifest = load_source_manifest(
        manifest_path
    )

    normalized: list[
        CompetitionResult
    ] = []

    for source in sources:

        metadata = find_source_metadata(
            source.source_file,
            manifest,
        )

        normalized.extend(
            normalize_source(
                source,
                metadata,
            )
        )

    return normalized