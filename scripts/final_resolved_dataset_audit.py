import json
from pathlib import Path
from collections import Counter, defaultdict


INPUT = Path(
    "data/final/competition_results_resolved.jsonl"
)


def valid_number(value):
    return (
        value is None
        or isinstance(value, (int, float))
    )


def audit():
    rows = [
        json.loads(line)
        for line in INPUT.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    required_fields = {
        "athlete_id",
        "resolved_athlete_id",
        "identity_confidence",
        "competition",
        "year",
        "division",
        "weight_class",
        "equipment",
    }

    confidence_counts = Counter()
    missing_required = Counter()
    invalid_numeric = []
    total_mismatches = []
    duplicate_keys = Counter()
    invalid_attempts = []
    missing_identity = []

    seen = defaultdict(list)

    attempt_fields = [
        "squat_1",
        "squat_2",
        "squat_3",
        "bench_1",
        "bench_2",
        "bench_3",
        "deadlift_1",
        "deadlift_2",
        "deadlift_3",
    ]

    best_fields = [
        "best_squat",
        "best_bench",
        "best_deadlift",
    ]

    for index, row in enumerate(rows, start=1):

        # ----------------------------------------------------
        # Required fields
        # ----------------------------------------------------

        for field in required_fields:
            value = row.get(field)

            if value is None or str(value).strip() == "":
                missing_required[field] += 1

        # ----------------------------------------------------
        # Identity
        # ----------------------------------------------------

        confidence = row.get(
            "identity_confidence"
        )

        confidence_counts[confidence] += 1

        if not row.get("resolved_athlete_id"):
            missing_identity.append(index)

        # ----------------------------------------------------
        # Numeric fields
        # ----------------------------------------------------

        numeric_fields = [
            "bodyweight",
            *attempt_fields,
            *best_fields,
            "total",
        ]

        for field in numeric_fields:

            value = row.get(field)

            if not valid_number(value):
                invalid_numeric.append(
                    (index, field, value)
                )

        # ----------------------------------------------------
        # Attempt sanity
        # ----------------------------------------------------

        for field in attempt_fields:

            value = row.get(field)

            if (
                value is not None
                and isinstance(value, (int, float))
                and value == 0
            ):
                invalid_attempts.append(
                    (index, field, value)
                )

        # ----------------------------------------------------
        # Total consistency
        # ----------------------------------------------------

        best_squat = row.get("best_squat")
        best_bench = row.get("best_bench")
        best_deadlift = row.get("best_deadlift")
        total = row.get("total")

        if (
            best_squat is not None
            and best_bench is not None
            and best_deadlift is not None
            and total is not None
        ):
            calculated = (
                best_squat
                + best_bench
                + best_deadlift
            )

            if abs(calculated - total) > 0.01:
                total_mismatches.append(
                    {
                        "line": index,
                        "stored": total,
                        "calculated": calculated,
                        "difference": total - calculated,
                        "athlete_id": row.get(
                            "resolved_athlete_id"
                        ),
                    }
                )

        # ----------------------------------------------------
        # Duplicate result identity
        # ----------------------------------------------------

        key = (
            row.get("resolved_athlete_id"),
            row.get("year"),
            row.get("competition"),
            row.get("division"),
            row.get("weight_class"),
            row.get("equipment"),
        )

        seen[key].append(index)

    # --------------------------------------------------------
    # Duplicate groups
    # --------------------------------------------------------

    duplicate_groups = {
        key: lines
        for key, lines in seen.items()
        if len(lines) > 1
    }

    duplicate_record_count = sum(
        len(lines)
        for lines in duplicate_groups.values()
    )

    # --------------------------------------------------------
    # Print report
    # --------------------------------------------------------

    print("=" * 60)
    print("FINAL RESOLVED DATASET AUDIT")
    print("=" * 60)

    print(
        "INPUT:",
        INPUT
    )

    print(
        "TOTAL RECORDS:",
        len(rows)
    )

    print()
    print("IDENTITY CONFIDENCE")
    print("-" * 60)

    for key, value in sorted(
        confidence_counts.items(),
        key=lambda x: str(x[0]),
    ):
        print(
            f"{key}: {value}"
        )

    print()
    print("REQUIRED FIELD CHECK")
    print("-" * 60)

    if missing_required:
        for field, count in sorted(
            missing_required.items()
        ):
            print(
                f"{field}: {count} missing"
            )
    else:
        print(
            "PASS: no required fields missing"
        )

    print()
    print("RESOLVED ID CHECK")
    print("-" * 60)

    print(
        "MISSING RESOLVED IDs:",
        len(missing_identity)
    )

    print()
    print("NUMERIC FIELD CHECK")
    print("-" * 60)

    print(
        "INVALID NUMERIC VALUES:",
        len(invalid_numeric)
    )

    print()
    print("ATTEMPT CHECK")
    print("-" * 60)

    print(
        "ZERO ATTEMPTS:",
        len(invalid_attempts)
    )

    print()
    print("TOTAL CONSISTENCY")
    print("-" * 60)

    print(
        "TOTAL MISMATCHES:",
        len(total_mismatches)
    )

    if total_mismatches:
        for item in total_mismatches[:10]:
            print(item)

    print()
    print("DUPLICATE RESULT CHECK")
    print("-" * 60)

    print(
        "DUPLICATE GROUPS:",
        len(duplicate_groups)
    )

    print(
        "RECORDS IN DUPLICATE GROUPS:",
        duplicate_record_count
    )

    if duplicate_groups:
        print()
        print("FIRST DUPLICATE GROUPS:")

        for key, lines in list(
            duplicate_groups.items()
        )[:10]:
            print(
                key,
                "LINES:",
                lines,
            )

    print()
    print("=" * 60)

    failures = (
        bool(missing_required)
        or bool(missing_identity)
        or bool(invalid_numeric)
        or bool(total_mismatches)
        or bool(duplicate_groups)
    )

    if failures:
        print(
            "AUDIT RESULT: FAIL"
        )
    else:
        print(
            "AUDIT RESULT: PASS"
        )

    print("=" * 60)


if __name__ == "__main__":
    audit()
