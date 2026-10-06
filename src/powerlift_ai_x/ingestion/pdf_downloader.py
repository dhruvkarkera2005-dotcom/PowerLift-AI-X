from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests


HEADERS = {
    "User-Agent": "PowerLift-AI-X/0.1.0",
}


def download_pdf(
    url: str,
    output_dir: Path,
) -> dict[str, str | int | bool]:
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = Path(
        urlparse(url).path
    ).name

    if not filename.lower().endswith(".pdf"):
        raise ValueError(
            f"Source URL is not a PDF: {url}"
        )

    output_path = output_dir / filename

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()

    content = response.content

    if not content.startswith(b"%PDF"):
        raise ValueError(
            f"Downloaded content is not a valid PDF: {url}"
        )

    output_path.write_bytes(content)

    sha256 = hashlib.sha256(content).hexdigest()

    return {
        "url": url,
        "path": str(output_path),
        "filename": filename,
        "status_code": response.status_code,
        "size_bytes": len(content),
        "sha256": sha256,
        "is_pdf": True,
    }