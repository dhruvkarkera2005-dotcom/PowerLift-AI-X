from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

import requests


MANIFEST_PATH = Path("data/verified_source_manifest.json")
RAW_DIR = Path("data/raw")

HEADERS = {
    "User-Agent": "PowerLift-AI-X/0.1.0",
}


def download_source(source: dict) -> dict:
    url = source["men_url"]

    filename = Path(urlparse(url).path).name

    if not filename.lower().endswith(".pdf"):
        return {
            **source,
            "download_status": "INVALID_FILENAME",
        }

    output_path = RAW_DIR / filename

    # Do not download the same file again.
    if output_path.exists():
        content = output_path.read_bytes()

        return {
            **source,
            "filename": filename,
            "local_path": str(output_path),
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "download_status": "ALREADY_EXISTS",
        }

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=60,
        )
        response.raise_for_status()

        content = response.content

        if not content.startswith(b"%PDF"):
            return {
                **source,
                "filename": filename,
                "download_status": "NOT_A_PDF",
            }

        output_path.write_bytes(content)

        return {
            **source,
            "filename": filename,
            "local_path": str(output_path),
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "download_status": "DOWNLOADED",
        }

    except requests.RequestException as exc:
        return {
            **source,
            "filename": filename,
            "download_status": "DOWNLOAD_FAILED",
            "error": str(exc),
        }


def main() -> None:
    sources = json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8",
        )
    )

    valid_sources = [
        source
        for source in sources
        if source.get("status") == "VALID"
    ]

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    print(
        f"Downloading {len(valid_sources)} "
        "verified PDF sources..."
    )
    print("=" * 70)

    for index, source in enumerate(
        valid_sources,
        start=1,
    ):
        print(
            f"[{index}/{len(valid_sources)}] "
            f"{source['year']} - "
            f"{source['competition']}"
        )

        result = download_source(source)

        results.append(result)

        print(
            f"    {result['download_status']}"
        )

        if result.get("filename"):
            print(
                f"    {result['filename']}"
            )

        print()

    output_path = Path(
        "data/downloaded_source_manifest.json"
    )

    output_path.write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    downloaded = sum(
        r["download_status"] == "DOWNLOADED"
        for r in results
    )

    existing = sum(
        r["download_status"] == "ALREADY_EXISTS"
        for r in results
    )

    failed = sum(
        r["download_status"]
        not in {"DOWNLOADED", "ALREADY_EXISTS"}
        for r in results
    )

    print("=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)
    print(f"Downloaded: {downloaded}")
    print(f"Already existed: {existing}")
    print(f"Failed/invalid: {failed}")
    print()
    print(f"Manifest: {output_path}")


if __name__ == "__main__":
    main()