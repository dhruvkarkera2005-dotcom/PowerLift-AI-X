from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader


SOURCE_MANIFEST = Path("data/downloaded_source_manifest.json")
OUTPUT_MANIFEST = Path("data/content_verified_source_manifest.json")


EXCLUDED_TERMS = (
    "women",
    "female",
    "girls",
    "blind",
    "differently abled",
    "differently-abled",
    "disabled",
    "disability",
    "para powerlifting",
    "para-powerlifting",
    "special olympics",
)


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)

    pages = []

    for page in reader.pages:
        pages.append(page.extract_text() or "")

    return "\n".join(pages)


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def detect_male_powerlifting_structure(text: str) -> bool:
    """
    Detect evidence that the PDF contains men's
    full-powerlifting result sections.

    Powerlifting India PDFs may identify men's sections
    through explicit wording or through standard men's
    weight-class headings such as:

        Open - 59kg
        Open - 66kg
        Sub Junior - 59kg
        Junior - 74kg
        Master 1 - 83kg
    """

    normalized = " ".join(text.lower().split())

    explicit_male = contains_any(
        normalized,
        (
            " men ",
            " male ",
            " men's ",
            "mens ",
            "men's ",
        ),
    )

    weight_class_section = bool(
        re.search(
            r"\b("
            r"open"
            r"|sub\s*junior"
            r"|junior"
            r"|senior"
            r"|masters?"
            r"|master\s*[1-5]"
            r")"
            r"\s*-\s*"
            r"\d+(?:\.\d+)?\s*kg\b",
            normalized,
        )
    )

    return (
        explicit_male
        or weight_class_section
    )


def verify_content(text: str) -> dict[str, object]:
    normalized = " ".join(text.lower().split())

    has_men = detect_male_powerlifting_structure(
        normalized
    )

    has_squat = any(
        term in normalized
        for term in (
            "squat",
            " sq ",
            "sq1",
            "sq2",
            "sq3",
        )
    )

    has_bench = any(
        term in normalized
        for term in (
            "bench press",
            "bench",
            " bp ",
            "bp1",
            "bp2",
            "bp3",
        )
    )

    has_deadlift = any(
        term in normalized
        for term in (
            "deadlift",
            "dead lift",
            " dl ",
            "dl1",
            "dl2",
            "dl3",
        )
    )

    has_total = bool(
        re.search(
            r"\btotal\b",
            normalized,
        )
    )

    has_place = bool(
        re.search(
            r"\bplace\b",
            normalized,
        )
    )

    excluded_category = contains_any(
        normalized,
        EXCLUDED_TERMS,
    )

    complete_sbd = (
        has_squat
        and has_bench
        and has_deadlift
        and has_total
        and has_place
    )

    # Strong positive evidence.
    if (
        has_men
        and complete_sbd
        and not excluded_category
    ):
        status = "VALID"

    # The PDF has powerlifting structure but needs
    # section-level inspection.
    elif complete_sbd:
        status = "REVIEW"

    # Partial powerlifting evidence.
    elif (
        has_squat
        or has_bench
        or has_deadlift
    ):
        status = "REVIEW"

    else:
        status = "REJECT"

    return {
        "content_status": status,
        "has_men": has_men,
        "has_squat": has_squat,
        "has_bench": has_bench,
        "has_deadlift": has_deadlift,
        "has_total": has_total,
        "has_place": has_place,
        "complete_sbd": complete_sbd,
        "has_excluded_category": excluded_category,
    }


def main() -> None:
    sources = json.loads(
        SOURCE_MANIFEST.read_text(
            encoding="utf-8"
        )
    )

    results = []

    counts = {
        "VALID": 0,
        "REVIEW": 0,
        "REJECT": 0,
        "ERROR": 0,
    }

    print(
        f"Verifying {len(sources)} downloaded PDFs..."
    )
    print("=" * 70)

    for index, source in enumerate(
        sources,
        start=1,
    ):
        pdf_path = Path(
            source.get("local_path", "")
        )

        print(
            f"[{index}/{len(sources)}] "
            f"{source['year']} - "
            f"{source['competition']}"
        )

        if not pdf_path.exists():
            updated = {
                **source,
                "content_status": "ERROR",
                "content_error": "FILE_NOT_FOUND",
            }

            counts["ERROR"] += 1
            results.append(updated)

            print("    ERROR: FILE_NOT_FOUND")
            print()
            continue

        try:
            reader = PdfReader(pdf_path)

            pages = len(reader.pages)

            text = extract_text(pdf_path)

            verification = verify_content(text)

            updated = {
                **source,
                **verification,
                "pages_checked": pages,
            }

            results.append(updated)

            status = verification[
                "content_status"
            ]

            counts[status] += 1

            print(f"    {status}")
            print(
                f"    Men's structure: "
                f"{verification['has_men']}"
            )
            print(
                f"    Squat: "
                f"{verification['has_squat']}"
            )
            print(
                f"    Bench: "
                f"{verification['has_bench']}"
            )
            print(
                f"    Deadlift: "
                f"{verification['has_deadlift']}"
            )
            print(
                f"    Total: "
                f"{verification['has_total']}"
            )
            print(
                f"    Place: "
                f"{verification['has_place']}"
            )
            print(
                f"    Excluded category: "
                f"{verification['has_excluded_category']}"
            )

        except Exception as exc:
            updated = {
                **source,
                "content_status": "ERROR",
                "content_error": str(exc),
            }

            counts["ERROR"] += 1
            results.append(updated)

            print(f"    ERROR: {exc}")

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
    print("CONTENT VERIFICATION COMPLETE")
    print("=" * 70)
    print(f"VALID: {counts['VALID']}")
    print(f"REVIEW: {counts['REVIEW']}")
    print(f"REJECT: {counts['REJECT']}")
    print(f"ERROR: {counts['ERROR']}")
    print()
    print(
        f"Manifest: {OUTPUT_MANIFEST}"
    )


if __name__ == "__main__":
    main()