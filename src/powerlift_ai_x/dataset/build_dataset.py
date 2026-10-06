from __future__ import annotations

from pathlib import Path

from powerlift_ai_x.dataset.writer import (
    write_canonical_dataset,
)
from powerlift_ai_x.normalization.competition_result_normalizer import (
    load_source_manifest,
    normalize_source,
)
from powerlift_ai_x.parsing.unified_parser import (
    parse_directory,
)


def _manifest_key(
    filename: str | Path,
) -> str:
    """
    Return a normalized filename key for manifest matching.

    Matching is case-insensitive and uses only the filename,
    not the directory path.
    """

    return Path(
        str(filename)
    ).name.strip().lower()


def _find_manifest_metadata(
    manifest: dict[str, dict],
    source_file: str | Path,
) -> dict:
    """
    Find manifest metadata corresponding to an extracted TXT.

    Extracted files normally use:

        something.txt

    while the manifest uses:

        something.pdf

    The lookup is normalized so Windows path/case differences
    cannot cause false mismatches.
    """

    extracted_name = Path(
        str(source_file)
    ).name

    expected_pdf = (
        Path(extracted_name).stem
        + ".pdf"
    )

    expected_key = _manifest_key(
        expected_pdf
    )

    # --------------------------------------------------------
    # Exact normalized filename match.
    # --------------------------------------------------------

    for filename, metadata in manifest.items():

        if _manifest_key(filename) == expected_key:
            return metadata

    # --------------------------------------------------------
    # No match.
    # --------------------------------------------------------

    raise ValueError(
        "No manifest entry found for "
        f"{extracted_name} "
        f"(expected PDF: {expected_pdf})"
    )


def build_dataset(
    extracted_directory: str | Path,
    manifest_path: str | Path,
    output_directory: str | Path,
) -> dict[str, object]:
    """
    Build the canonical PowerLift-AI-X dataset.

    Pipeline:

        extracted TXT files
                ↓
        unified parser
                ↓
        normalization
                ↓
        CompetitionResult objects
                ↓
        canonical JSONL + CSV

    Incomplete and REVIEW rows are excluded from
    the canonical complete-result dataset.
    """

    extracted_directory = Path(
        extracted_directory
    )

    manifest_path = Path(
        manifest_path
    )

    output_directory = Path(
        output_directory
    )

    # --------------------------------------------------------
    # Parse all extracted sources.
    # --------------------------------------------------------

    sources = parse_directory(
        extracted_directory
    )

    # --------------------------------------------------------
    # Load source manifest.
    # --------------------------------------------------------

    manifest = load_source_manifest(
        manifest_path
    )

    # --------------------------------------------------------
    # Normalize sources.
    # --------------------------------------------------------

    normalized = []

    source_count = 0
    parsed_source_count = 0
    incomplete_count = 0
    review_count = 0

    for source in sources:

        source_count += 1

        # ----------------------------------------------------
        # Resolve TXT → PDF manifest metadata.
        # ----------------------------------------------------

        metadata = _find_manifest_metadata(
            manifest,
            source.source_file,
        )

        # ----------------------------------------------------
        # Count parser statuses.
        # ----------------------------------------------------

        source_has_parsed_rows = False

        for result in source.results:

            status = result.get(
                "status"
            )

            if status == "PARSED":
                source_has_parsed_rows = True

            elif status == "INCOMPLETE":
                incomplete_count += 1

            elif status == "REVIEW":
                review_count += 1

        if source_has_parsed_rows:
            parsed_source_count += 1

        # ----------------------------------------------------
        # Normalize successfully parsed rows.
        # ----------------------------------------------------

        normalized_source = normalize_source(
            source,
            metadata,
        )

        normalized.extend(
            normalized_source
        )

    # --------------------------------------------------------
    # Write canonical dataset.
    # --------------------------------------------------------

    dataset_metadata = (
        write_canonical_dataset(
            normalized,
            output_directory,
        )
    )

    # --------------------------------------------------------
    # Return build metadata.
    # --------------------------------------------------------

    return {
        "source_count": source_count,
        "parsed_source_count": parsed_source_count,
        "incomplete_count": incomplete_count,
        "review_count": review_count,
        "normalized_count": len(normalized),
        **dataset_metadata,
    }


def main() -> None:
    """
    Build the production canonical dataset.
    """

    result = build_dataset(
        extracted_directory="data/extracted",
        manifest_path="data/final_source_manifest.json",
        output_directory="data/final",
    )

    print("=" * 50)
    print("POWERLIFT-AI-X DATASET BUILD")
    print("=" * 50)

    print(
        f"SOURCES:              "
        f"{result['source_count']}"
    )

    print(
        f"PARSED SOURCES:       "
        f"{result['parsed_source_count']}"
    )

    print(
        f"INCOMPLETE ROWS:      "
        f"{result['incomplete_count']}"
    )

    print(
        f"REVIEW ROWS:          "
        f"{result['review_count']}"
    )

    print(
        f"NORMALIZED RESULTS:   "
        f"{result['normalized_count']}"
    )

    print(
        f"JSONL:                "
        f"{result['jsonl_path']}"
    )

    print(
        f"CSV:                  "
        f"{result['csv_path']}"
    )

    print("=" * 50)


if __name__ == "__main__":
    main()