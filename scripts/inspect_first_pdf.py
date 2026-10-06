from pathlib import Path

from pypdf import PdfReader


PDF_PATH = Path("data/raw/20250224104722ab.pdf")


def main() -> None:
    reader = PdfReader(PDF_PATH)

    print(f"PDF: {PDF_PATH}")
    print(f"Pages: {len(reader.pages)}")
    print("=" * 80)

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        print()
        print(f"===== PAGE {page_number} =====")
        print(text)


if __name__ == "__main__":
    main()