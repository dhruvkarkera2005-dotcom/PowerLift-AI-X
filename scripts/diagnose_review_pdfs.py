from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader


MANIFEST = Path(
    "data/content_verified_source_manifest.json"
)


def main() -> None:
    sources = json.loads(
        MANIFEST.read_text(
            encoding="utf-8"
        )
    )

    review_sources = [
        source
        for source in sources
        if source.get("content_status") == "REVIEW"
    ]

    print(
        f"Review PDFs found: {len(review_sources)}"
    )
    print("=" * 80)

    # Inspect only the first 5 REVIEW PDFs.
    for index, source in enumerate(
        review_sources[:5],
        start=1,
    ):
        pdf_path = Path(
            source.get("local_path", "")
        )

        print()
        print(
            f"========== REVIEW PDF {index} =========="
        )
        print(
            f"Year: {source['year']}"
        )
        print(
            f"Competition: {source['competition']}"
        )
        print(
            f"File: {pdf_path}"
        )
        print("=" * 80)

        if not pdf_path.exists():
            print("FILE NOT FOUND")
            continue

        reader = PdfReader(pdf_path)

        print(f"Pages: {len(reader.pages)}")

        for page_number, page in enumerate(
            reader.pages[:2],
            start=1,
        ):
            text = page.extract_text() or ""

            print()
            print(
                f"----- PAGE {page_number} -----"
            )

            # Show first 60 non-empty lines.
            lines = [
                line.strip()
                for line in text.splitlines()
                if line.strip()
            ]

            for line in lines[:60]:
                print(line)

        print()


if __name__ == "__main__":
    main()