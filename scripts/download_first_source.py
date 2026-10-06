from pathlib import Path

from powerlift_ai_x.ingestion.pdf_downloader import (
    download_pdf,
)


URL = (
    "https://powerliftingindia.net/"
    "upload/results/20250224104722ab.pdf"
)

OUTPUT_DIR = Path("data/raw")


def main() -> None:
    result = download_pdf(
        url=URL,
        output_dir=OUTPUT_DIR,
    )

    print("PDF downloaded successfully")
    print(f"Filename: {result['filename']}")
    print(f"Path: {result['path']}")
    print(f"HTTP status: {result['status_code']}")
    print(f"Size: {result['size_bytes']} bytes")
    print(f"SHA-256: {result['sha256']}")
    print(f"Valid PDF signature: {result['is_pdf']}")


if __name__ == "__main__":
    main()