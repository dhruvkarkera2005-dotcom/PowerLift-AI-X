from __future__ import annotations

import json
from pathlib import Path


INPUT_MANIFEST = Path(
    "data/content_verified_source_manifest.json"
)

OUTPUT_MANIFEST = Path(
    "data/final_source_manifest.json"
)

ACCEPTED_STATUSES = {
    "VALID",
}


def main() -> None:
    sources = json.loads(
        INPUT_MANIFEST.read_text(
            encoding="utf-8"
        )
    )

    accepted = [
        source
        for source in sources
        if source.get("content_status")
        in ACCEPTED_STATUSES
    ]

    rejected = [
        source
        for source in sources
        if source.get("content_status")
        not in ACCEPTED_STATUSES
    ]

    OUTPUT_MANIFEST.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_MANIFEST.write_text(
        json.dumps(
            accepted,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("=" * 70)
    print("FINAL SOURCE MANIFEST")
    print("=" * 70)
    print(f"Accepted sources: {len(accepted)}")
    print(f"Not accepted: {len(rejected)}")
    print()
    print(f"Manifest: {OUTPUT_MANIFEST}")


if __name__ == "__main__":
    main()