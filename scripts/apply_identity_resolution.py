from pathlib import Path

from powerlift_ai_x.identity.applier import (
    apply_identity_resolution_file,
)


INPUT_PATH = Path(
    "data/final/competition_results.jsonl"
)

RESOLUTION_PATH = Path(
    "data/final/athlete_identity_resolution.json"
)

OUTPUT_PATH = Path(
    "data/final/competition_results_resolved.jsonl"
)


def main() -> None:
    result = apply_identity_resolution_file(
        input_path=INPUT_PATH,
        resolution_path=RESOLUTION_PATH,
        output_path=OUTPUT_PATH,
    )

    print("=" * 50)
    print("IDENTITY RESOLUTION APPLICATION")
    print("=" * 50)

    print(
        f"TOTAL:       {result['total']}"
    )

    print(
        f"UNIQUE:      {result['unique']}"
    )

    print(
        f"SAME:        {result['same']}"
    )

    print(
        f"SPLIT:       {result['split']}"
    )

    print(
        f"UNRESOLVED:  {result['unresolved']}"
    )

    print(
        f"OUTPUT:      {OUTPUT_PATH}"
    )

    print("=" * 50)


if __name__ == "__main__":
    main()
