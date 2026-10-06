from __future__ import annotations

import json
from pathlib import Path

from powerlift_ai_x.ingestion.source_discovery import (
    discover_sources,
)


OUTPUT = Path("data/source_manifest.json")


def main() -> None:
    sources = discover_sources()

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            sources,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Discovered {len(sources)} candidate "
        "men's full-powerlifting sources."
    )

    print(f"Manifest: {OUTPUT}")


if __name__ == "__main__":
    main()