from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


EXTRACTED_DIR = Path("data/extracted")
OUTPUT_PATH = Path("data/extracted_format_profile.json")


def normalize_line(line: str) -> str:
    line = line.lower().strip()

    # Normalize numbers so two otherwise identical
    # table headers aren't separated by values.
    line = re.sub(r"\d+(?:\.\d+)?", "#", line)

    # Normalize whitespace.
    line = re.sub(r"\s+", " ", line)

    return line


def detect_features(text: str) -> dict[str, bool]:
    normalized = text.lower()

    return {
        "has_rank": bool(
            re.search(r"\brank\b", normalized)
        ),
        "has_name": bool(
            re.search(r"\bname\b", normalized)
        ),
        "has_bodyweight": bool(
            re.search(
                r"\b(bodyweight|bd\.?\s*wt|bw)\b",
                normalized,
            )
        ),
        "has_squat": bool(
            re.search(
                r"\b(sq1|sq2|sq3|squat)\b",
                normalized,
            )
        ),
        "has_bench": bool(
            re.search(
                r"\b(bp1|bp2|bp3|bench)\b",
                normalized,
            )
        ),
        "has_deadlift": bool(
            re.search(
                r"\b(dl1|dl2|dl3|deadlift)\b",
                normalized,
            )
        ),
        "has_total": bool(
            re.search(r"\btotal\b", normalized)
        ),
    }


def find_header_lines(text: str) -> list[str]:
    headers = []

    for line in text.splitlines():
        normalized = normalize_line(line)

        score = 0

        for keyword in (
            "rank",
            "name",
            "dob",
            "state",
            "bd. wt",
            "bodyweight",
            "sq1",
            "sq2",
            "sq3",
            "bp1",
            "bp2",
            "bp3",
            "dl1",
            "dl2",
            "dl3",
            "total",
            "place",
        ):
            if keyword in normalized:
                score += 1

        if score >= 4:
            headers.append(line.strip())

    return headers


def create_format_signature(
    features: dict[str, bool],
    headers: list[str],
) -> str:
    feature_part = "|".join(
        key
        for key, value in features.items()
        if value
    )

    header_part = ""

    if headers:
        header_part = normalize_line(
            headers[0]
        )

    raw_signature = (
        f"{feature_part}||{header_part}"
    )

    return hashlib.sha256(
        raw_signature.encode("utf-8")
    ).hexdigest()[:12]


def main() -> None:
    files = sorted(
        EXTRACTED_DIR.glob("*.txt")
    )

    profiles = []

    format_groups: dict[
        str,
        list[str],
    ] = {}

    print(
        f"Profiling {len(files)} extracted files..."
    )
    print("=" * 70)

    for index, path in enumerate(
        files,
        start=1,
    ):
        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        features = detect_features(text)
        headers = find_header_lines(text)

        signature = create_format_signature(
            features,
            headers,
        )

        profile = {
            "file": path.name,
            "format_signature": signature,
            "features": features,
            "header_examples": headers[:5],
            "characters": len(text),
            "lines": len(text.splitlines()),
        }

        profiles.append(profile)

        format_groups.setdefault(
            signature,
            [],
        ).append(path.name)

        print(
            f"[{index}/{len(files)}] "
            f"{path.name} -> {signature}"
        )

    output = {
        "files_profiled": len(files),
        "format_count": len(format_groups),
        "formats": [
            {
                "format_signature": signature,
                "file_count": len(file_names),
                "files": file_names,
            }
            for signature, file_names
            in format_groups.items()
        ],
        "profiles": profiles,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 70)
    print("FORMAT PROFILING COMPLETE")
    print("=" * 70)
    print(f"Files profiled: {len(files)}")
    print(
        f"Format signatures: "
        f"{len(format_groups)}"
    )

    for signature, file_names in (
        format_groups.items()
    ):
        print(
            f"  {signature}: "
            f"{len(file_names)} files"
        )

    print()
    print(f"Report: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()