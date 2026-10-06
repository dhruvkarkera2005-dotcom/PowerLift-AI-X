from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from powerlift_ai_x.parsing.format2_parser import (
    parse_format2_text,
)
from powerlift_ai_x.parsing.result_parser import (
    parse_format1_text,
)


FINAL_MANIFEST = Path(
    "data/final_source_manifest.json"
)

EXTRACTED_DIR = Path(
    "data/extracted"
)

OUTPUT_MANIFEST = Path(
    "data/parsed_source_manifest.json"
)


def load_manifest() -> list[dict[str, object]]:
    if not FINAL_MANIFEST.exists():
        raise FileNotFoundError(
            f"Manifest not found: {FINAL_MANIFEST}"
        )

    return json.loads(
        FINAL_MANIFEST.read_text(
            encoding="utf-8"
        )
    )


def load_text(local_path: str) -> str:
    path = Path(local_path)

    if not path.exists():
        # Some manifests may contain paths relative
        # to the project root.
        path = Path(
            local_path.replace("/", "\\")
        )

    if not path.exists():
        raise FileNotFoundError(
            f"Extracted file not found: {local_path}"
        )

    return path.read_text(
        encoding="utf-8",
        errors="replace",
    )


def detect_parser(text: str) -> str:
    """
    Detect which parser should process the extracted text.

    Format 2 contains the Coeff / IPF GL columns.

    Format 1 uses the older:
        Place Name DOB Team Lot Bd. Wt.
        SQ1 SQ2 SQ3 Best [PL] ...
    structure without Coeff.
    """

    normalized = " ".join(
        text.lower().split()
    )

    if (
        "coeff." in normalized
        and "ipf gl points" in normalized
    ):
        return "FORMAT2"

    return "FORMAT1"


def parse_source(
    source: dict[str, object],
) -> dict[str, object]:

    local_path = str(
        source.get("local_path", "")
    )

    text = load_text(local_path)

    parser_name = detect_parser(text)

    if parser_name == "FORMAT2":
        parsed_rows = parse_format2_text(
            text
        )
    else:
        parsed_rows = parse_format1_text(
            text
        )

    parsed_count = 0
    incomplete_count = 0

    for item in parsed_rows:
        status = item.get("status")

        if status == "PARSED":
            parsed_count += 1

        elif status == "INCOMPLETE":
            incomplete_count += 1

    return {
        **source,
        "parser": parser_name,
        "status": "SUCCESS",
        "result_count": len(parsed_rows),
        "parsed_count": parsed_count,
        "incomplete_count": incomplete_count,
        "results": parsed_rows,
    }


def main() -> None:

    sources = load_manifest()

    print("=" * 70)
    print("BATCH PARSING")
    print("=" * 70)
    print(
        f"Sources to parse: {len(sources)}"
    )
    print()

    results: list[dict[str, object]] = []

    parser_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()

    total_results = 0
    total_parsed = 0
    total_incomplete = 0

    for index, source in enumerate(
        sources,
        start=1,
    ):

        year = source.get(
            "year",
            "?",
        )

        competition = source.get(
            "competition",
            "?",
        )

        local_path = source.get(
            "local_path",
            "",
        )

        print(
            f"[{index}/{len(sources)}] "
            f"{year} - {competition}"
        )

        try:

            parsed = parse_source(
                source
            )

            results.append(
                parsed
            )

            parser_name = str(
                parsed["parser"]
            )

            result_count = int(
                parsed["result_count"]
            )

            parsed_count = int(
                parsed["parsed_count"]
            )

            incomplete_count = int(
                parsed["incomplete_count"]
            )

            parser_counts[
                parser_name
            ] += 1

            status_counts[
                "SUCCESS"
            ] += 1

            total_results += result_count
            total_parsed += parsed_count
            total_incomplete += (
                incomplete_count
            )

            print(
                f"    Parser: {parser_name}"
            )

            print(
                f"    Results: {result_count}"
            )

            print(
                f"    PARSED: {parsed_count}"
            )

            print(
                f"    INCOMPLETE: "
                f"{incomplete_count}"
            )

        except Exception as exc:

            error_result = {
                **source,
                "parser": None,
                "status": "ERROR",
                "error": str(exc),
                "result_count": 0,
                "parsed_count": 0,
                "incomplete_count": 0,
                "results": [],
            }

            results.append(
                error_result
            )

            status_counts[
                "ERROR"
            ] += 1

            print(
                f"    ERROR: {exc}"
            )

        print()

    OUTPUT_MANIFEST.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_MANIFEST.write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("=" * 70)
    print("BATCH PARSING COMPLETE")
    print("=" * 70)

    print(
        f"Sources: {len(sources)}"
    )

    print(
        f"SUCCESS: "
        f"{status_counts['SUCCESS']}"
    )

    print(
        f"ERROR: "
        f"{status_counts['ERROR']}"
    )

    print()

    print(
        "PARSERS:"
    )

    for parser_name, count in sorted(
        parser_counts.items()
    ):
        print(
            f"  {parser_name}: {count}"
        )

    print()

    print(
        f"RESULTS: {total_results}"
    )

    print(
        f"PARSED: {total_parsed}"
    )

    print(
        f"INCOMPLETE: "
        f"{total_incomplete}"
    )

    print()

    print(
        f"Manifest: "
        f"{OUTPUT_MANIFEST}"
    )


if __name__ == "__main__":
    main()