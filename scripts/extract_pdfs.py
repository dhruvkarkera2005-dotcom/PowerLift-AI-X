from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader


SOURCE_MANIFEST = Path(
    "data/final_source_manifest.json"
)

OUTPUT_DIR = Path(
    "data/extracted"
)

OUTPUT_MANIFEST = Path(
    "data/extracted_manifest.json"
)


def extract_pdf(pdf_path: Path) -> tuple[str, int]:
    reader = PdfReader(pdf_path)

    pages: list[str] = []

    for page in reader.pages:
        pages.append(
            page.extract_text() or ""
        )

    return "\n\n".join(pages), len(reader.pages)


def main() -> None:
    sources = json.loads(
        SOURCE_MANIFEST.read_text(
            encoding="utf-8"
        )
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results: list[dict] = []

    print(
        f"Extracting {len(sources)} PDFs..."
    )
    print("=" * 70)

    for index, source in enumerate(
        sources,
        start=1,
    ):
        pdf_path = Path(
            source["local_path"]
        )

        filename = pdf_path.stem + ".txt"
        output_path = OUTPUT_DIR / filename

        print(
            f"[{index}/{len(sources)}] "
            f"{source['year']} - "
            f"{source['competition']}"
        )

        try:
            text, page_count = extract_pdf(
                pdf_path
            )

            output_path.write_text(
                text,
                encoding="utf-8",
            )

            character_count = len(text)

            result = {
                **source,
                "extraction_status": "SUCCESS",
                "extracted_path": str(
                    output_path
                ),
                "pages": page_count,
                "characters": character_count,
            }

            results.append(result)

            print(
                f"    SUCCESS | "
                f"{page_count} pages | "
                f"{character_count} characters"
            )

        except Exception as exc:
            result = {
                **source,
                "extraction_status": "FAILED",
                "extraction_error": str(exc),
            }

            results.append(result)

            print(
                f"    FAILED | {exc}"
            )

        print()

    OUTPUT_MANIFEST.write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    success = sum(
        item["extraction_status"]
        == "SUCCESS"
        for item in results
    )

    failed = sum(
        item["extraction_status"]
        == "FAILED"
        for item in results
    )

    print("=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"SUCCESS: {success}")
    print(f"FAILED:  {failed}")
    print()
    print(
        f"Output directory: {OUTPUT_DIR}"
    )
    print(
        f"Manifest: {OUTPUT_MANIFEST}"
    )


if __name__ == "__main__":
    main()