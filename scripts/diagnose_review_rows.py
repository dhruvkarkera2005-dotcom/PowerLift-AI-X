from __future__ import annotations

from pathlib import Path

from powerlift_ai_x.parsing.result_parser import parse_format1_text


EXTRACTED_FILE = Path(
    "data/extracted/20190930045738ab.txt"
)


def main() -> None:
    text = EXTRACTED_FILE.read_text(
        encoding="utf-8"
    )

    results = parse_format1_text(text)

    reviews = [
        result
        for result in results
        if result["status"] == "REVIEW"
    ]

    print(
        f"Review rows found: {len(reviews)}"
    )
    print("=" * 80)

    for index, result in enumerate(
        reviews,
        start=1,
    ):
        print()
        print(
            f"REVIEW ROW {index}"
        )
        print("-" * 80)

        print(
            "Weight class:",
            result.get("weight_class"),
        )

        print(
            "Division:",
            result.get("division"),
        )

        print(
            "Raw line:",
            result.get("raw_line"),
        )


if __name__ == "__main__":
    main()