from __future__ import annotations

import json
from pathlib import Path

import requests


MANIFEST_PATH = Path("data/source_manifest.json")
OUTPUT_PATH = Path("data/verified_source_manifest.json")

HEADERS = {
    "User-Agent": "PowerLift-AI-X/0.1.0",
}


def verify_url(url: str) -> dict[str, object]:
    if not url or not url.lower().endswith(".pdf"):
        return {
            "status": "INVALID",
            "http_status": None,
            "content_type": None,
            "size_bytes": 0,
        }

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
            stream=True,
        )

        http_status = response.status_code
        content_type = response.headers.get(
            "Content-Type",
            "",
        )

        if http_status != 200:
            return {
                "status": "UNAVAILABLE",
                "http_status": http_status,
                "content_type": content_type,
                "size_bytes": 0,
            }

        first_bytes = next(
            response.iter_content(chunk_size=8),
            b"",
        )

        if not first_bytes.startswith(b"%PDF"):
            return {
                "status": "INVALID",
                "http_status": http_status,
                "content_type": content_type,
                "size_bytes": 0,
            }

        return {
            "status": "VALID",
            "http_status": http_status,
            "content_type": content_type,
            "size_bytes": 0,
        }

    except requests.RequestException as exc:
        return {
            "status": "UNAVAILABLE",
            "http_status": None,
            "content_type": None,
            "size_bytes": 0,
            "error": str(exc),
        }


def main() -> None:
    sources = json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8",
        )
    )

    verified = []

    counts = {
        "VALID": 0,
        "INVALID": 0,
        "UNAVAILABLE": 0,
        "REVIEW": 0,
    }

    for index, source in enumerate(
        sources,
        start=1,
    ):
        url = source.get("men_url", "")

        print(
            f"[{index}/{len(sources)}] "
            f"{source['year']} - "
            f"{source['competition']}"
        )

        result = verify_url(url)

        updated = {
            **source,
            **result,
        }

        verified.append(updated)

        status = result["status"]
        counts[status] += 1

        print(f"    {status}")
        print(f"    {url}")
        print()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            verified,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)

    for status, count in counts.items():
        print(f"{status}: {count}")

    print()
    print(f"Manifest: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()