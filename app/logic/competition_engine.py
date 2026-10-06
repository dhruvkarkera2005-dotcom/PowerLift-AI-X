from __future__ import annotations

import re
from functools import lru_cache
from typing import Optional

import pandas as pd

from app.services.athlete_data_service import AthleteDataService


# ============================================================
# VALIDATION / CONSTANTS
# ============================================================

VALID_TIERS = {
    "State",
    "National",
    "International",
}

VALID_DIVISIONS = {
    "Sub Junior",
    "Junior",
    "Open",
    "Master 1",
    "Master 2",
    "Master 3",
    "Master 4",
}

MEN_WEIGHT_CLASSES = (
    53,
    59,
    66,
    74,
    83,
    93,
    105,
    120,
    120,
)

ALL_MEN_CATEGORIES = (
    "Men 53 kg",
    "Men 59 kg",
    "Men 66 kg",
    "Men 74 kg",
    "Men 83 kg",
    "Men 93 kg",
    "Men 105 kg",
    "Men 120 kg",
    "Men 120+ kg",
)


# ============================================================
# DATA SERVICE
# ============================================================

@lru_cache(maxsize=1)
def _get_data_service() -> AthleteDataService:
    """Return one cached real-data service for the Streamlit process.

    The service loads the canonical/ML dataset from disk. Recreating it for
    every engine query makes Outlook unnecessarily slow, especially when
    several historical fallback queries are performed.
    """
    return AthleteDataService()


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def _normalise_equipment(value: object) -> Optional[str]:
    """Normalize equipment labels used by the real dataset."""
    if value is None:
        return None

    text = str(value).strip().upper()

    aliases = {
        "CLASSIC": "CLASSIC",
        "RAW": "CLASSIC",
        "RAW CLASSIC": "CLASSIC",
        "EQUIPPED": "EQUIPPED",
    }

    return aliases.get(text, text)


def _normalise_division(value: object) -> Optional[str]:
    """Normalize division labels without inventing a division."""
    if value is None:
        return None

    text = str(value).strip()

    aliases = {
        "SUBJUNIOR": "Sub Junior",
        "SUB JUNIOR": "Sub Junior",
        "SUB-JUNIOR": "Sub Junior",
        "JUNIOR": "Junior",
        "OPEN": "Open",
        "MASTER 1": "Master 1",
        "MASTER 2": "Master 2",
        "MASTER 3": "Master 3",
        "MASTER 4": "Master 4",
    }

    return aliases.get(text.upper(), text)


def _parse_category(category: str) -> tuple[str, int]:
    """
    Convert a UI category such as 'Men 83 kg' into sex/category
    context and the numeric weight class.
    """
    match = re.fullmatch(
        r"Men\s+(\d+)(\+?)\s*kg",
        str(category).strip(),
        flags=re.IGNORECASE,
    )

    if not match:
        raise ValueError(f"Unsupported category: {category}")

    weight_class = int(match.group(1))
    plus = match.group(2)

    if plus:
        if weight_class != 120:
            raise ValueError(f"Unsupported category: {category}")
        return "Men", 120

    if weight_class not in MEN_WEIGHT_CLASSES:
        raise ValueError(f"Unsupported category: {category}")

    return "Men", weight_class


def _validate_category(category: str) -> None:
    _parse_category(category)


def _validate_tier(meet_tier: str) -> None:
    if str(meet_tier).strip() not in VALID_TIERS:
        raise ValueError(
            f"Unsupported meet tier: {meet_tier}"
        )


# ============================================================
# REAL DATA ACCESS
# ============================================================

def _get_real_results(
    category: str,
    year: Optional[int] = None,
    before_year: Optional[int] = None,
    division: Optional[str] = None,
    equipment: Optional[str] = None,
    competition: Optional[str] = None,
    region: Optional[str] = None,
) -> pd.DataFrame:
    """
    Load real competition records from AthleteDataService.

    Important:
    - No synthetic competitors are created here.
    - No future competitor totals are fabricated.
    - Competition/region are treated as optional scope hints because
      the canonical dataset does not currently contain a normalized
      meet-tier/region field.
    """
    _, weight_class = _parse_category(category)

    service = _get_data_service()

    kwargs: dict[str, object] = {
        "weight_class": weight_class,
    }

    if year is not None:
        kwargs["year"] = int(year)

    if before_year is not None:
        kwargs["before_year"] = int(before_year)

    normalized_division = _normalise_division(division)
    if normalized_division is not None:
        kwargs["division"] = normalized_division

    normalized_equipment = _normalise_equipment(equipment)
    if normalized_equipment is not None:
        kwargs["equipment"] = normalized_equipment

    # Try an exact competition filter first only when explicitly
    # requested. If it produces no records, the caller can fall back
    # to the category/year field rather than incorrectly reporting
    # that historical data does not exist.
    if competition:
        kwargs["competition"] = str(competition)

    if region:
        # AthleteDataService only applies this if a region column exists.
        kwargs["region"] = str(region)

    try:
        result = service.get_competition_results(**kwargs)
    except TypeError:
        # Keep compatibility with an older AthleteDataService signature.
        kwargs.pop("region", None)
        result = service.get_competition_results(**kwargs)

    if result is None:
        return pd.DataFrame()

    return result.copy()


def _to_engine_columns(
    df: pd.DataFrame,
    *,
    requested_year: int,
    status: str,
    benchmark_year: Optional[int] = None,
) -> pd.DataFrame:
    """
    Adapt canonical real-data columns to the legacy frontend engine
    column contract.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "name",
                "athlete_name",
                "athlete_id",
                "total_kg",
                "wilks_or_gl",
                "placing",
                "place",
                "year",
                "competition",
                "division",
                "weight_class",
                "equipment",
                "bodyweight",
                "best_squat",
                "best_bench",
                "best_deadlift",
                "data_status",
                "benchmark_year",
            ]
        )

    result = df.copy()

    # Canonical service columns.
    if "athlete_name" in result.columns:
        result["name"] = result["athlete_name"].astype(str)
    elif "name" not in result.columns:
        result["name"] = "Unknown athlete"

    if "place" in result.columns:
        result["placing"] = pd.to_numeric(
            result["place"],
            errors="coerce",
        )
    elif "placing" not in result.columns:
        result["placing"] = pd.NA

    if "total" in result.columns:
        result["total_kg"] = pd.to_numeric(
            result["total"],
            errors="coerce",
        )
    elif "total_kg" in result.columns:
        result["total_kg"] = pd.to_numeric(
            result["total_kg"],
            errors="coerce",
        )
    else:
        result["total_kg"] = pd.NA

    # The canonical dataset does not currently contain Wilks/GL.
    # Keep the legacy column so the frontend remains compatible.
    if "wilks_or_gl" not in result.columns:
        result["wilks_or_gl"] = pd.NA

    if "weight_class" in result.columns:
        result["weight_class"] = pd.to_numeric(
            result["weight_class"],
            errors="coerce",
        )

    if "equipment" in result.columns:
        result["equipment"] = result["equipment"].map(
            _normalise_equipment
        )

    if "division" in result.columns:
        result["division"] = result["division"].map(
            _normalise_division
        )

    result["data_status"] = status

    if benchmark_year is None:
        benchmark_year = requested_year

    result["benchmark_year"] = int(benchmark_year)

    # Preserve the actual historical year in the table.
    if "year" in result.columns:
        result["year"] = pd.to_numeric(
            result["year"],
            errors="coerce",
        )

    sort_columns = [
        column
        for column in (
            "total_kg",
            "placing",
            "name",
        )
        if column in result.columns
    ]

    ascending = [
        False if column == "total_kg" else True
        for column in sort_columns
    ]

    if sort_columns:
        result = result.sort_values(
            sort_columns,
            ascending=ascending,
            na_position="last",
        )

    return result.reset_index(drop=True)


def _competition_hint_match(
    df: pd.DataFrame,
    meet_tier: str,
    competition: Optional[str],
) -> pd.DataFrame:
    """
    Apply a competition hint without making the frontend dependent on
    an exact historical meet name.

    Example:
        Planner: 'National Powerlifting Championship'
        Dataset: 'National Classic Powerlifting Championship 2019'

    An exact match is preferred. If unavailable, a tier-name match is
    attempted. If that also fails, the original real field is retained.
    """
    if df.empty or "competition" not in df.columns:
        return df

    if competition:
        exact = df[
            df["competition"].astype(str).str.strip().eq(
                str(competition).strip()
            )
        ].copy()

        if not exact.empty:
            return exact

    tier = str(meet_tier).strip().lower()

    if tier == "national":
        hinted = df[
            df["competition"]
            .astype(str)
            .str.contains("national", case=False, na=False)
        ].copy()

        if not hinted.empty:
            return hinted

    elif tier == "international":
        hinted = df[
            df["competition"]
            .astype(str)
            .str.contains(
                "international|world|asia|asian",
                case=False,
                regex=True,
                na=False,
            )
        ].copy()

        if not hinted.empty:
            return hinted

    return df


# ============================================================
# REAL-DATA SCOPE FALLBACK
# ============================================================

def _get_best_real_results(
    *,
    category: str,
    meet_tier: str,
    year: Optional[int] = None,
    before_year: Optional[int] = None,
    division: Optional[str] = None,
    equipment: Optional[str] = None,
    competition: Optional[str] = None,
    region: Optional[str] = None,
) -> tuple[pd.DataFrame, str]:
    """
    Return the most specific real-data field that actually exists.

    Fallback order:
      1. exact division + equipment
      2. same division, any equipment
      3. same equipment, any division
      4. same weight class, any division/equipment

    This never creates data.  The returned scope label lets the
    frontend disclose when a broader benchmark was required.
    """
    requested_division = _normalise_division(division)
    requested_equipment = _normalise_equipment(equipment)

    scopes: list[tuple[str, Optional[str], Optional[str]]] = []

    scopes.append((
        "exact division + equipment",
        requested_division,
        requested_equipment,
    ))

    if requested_division is not None:
        scopes.append((
            "same division, any equipment",
            requested_division,
            None,
        ))

    if requested_equipment is not None:
        scopes.append((
            "same equipment, any division",
            None,
            requested_equipment,
        ))

    scopes.append((
        "same weight class, any division/equipment",
        None,
        None,
    ))

    seen: set[tuple[Optional[str], Optional[str]]] = set()

    for label, scope_division, scope_equipment in scopes:
        key = (scope_division, scope_equipment)
        if key in seen:
            continue
        seen.add(key)

        result = _get_real_results(
            category=category,
            year=year,
            before_year=before_year,
            division=scope_division,
            equipment=scope_equipment,
            competition=competition,
            region=region,
        )

        if not result.empty:
            return result, label

        # The Planner meet name is a UI label and may not exactly match
        # the historical competition title (for example, the dataset
        # may contain "National Classic Powerlifting Championship 2019").
        # If the hinted meet/region produced no rows, retry the same
        # category scope without those hints before widening division or
        # equipment. This still uses only real records.
        if competition or region:
            result = _get_real_results(
                category=category,
                year=year,
                before_year=before_year,
                division=scope_division,
                equipment=scope_equipment,
            )

            if not result.empty:
                return result, label

    return pd.DataFrame(), "no real data"


# ============================================================
# COMPETITOR FIELD
# ============================================================

def get_competitors(
    category: str,
    meet_tier: str,
    year: int,
    competition: str | None = None,
    region: str | None = None,
    division: str | None = None,
    equipment: str | None = None,
) -> pd.DataFrame:
    """Return the best available real historical competitive field."""
    _validate_category(category)
    _validate_tier(meet_tier)

    target_year = int(year)

    target, scope = _get_best_real_results(
        category=category,
        meet_tier=meet_tier,
        year=target_year,
        division=division,
        equipment=equipment,
        competition=competition,
        region=region,
    )

    if not target.empty:
        result = _to_engine_columns(
            target,
            requested_year=target_year,
            status=(
                "historical_real"
                if scope == "exact division + equipment"
                else "historical_real_broader_benchmark"
            ),
            benchmark_year=target_year,
        )
        result["scope_status"] = scope
        return result

    history, scope = _get_best_real_results(
        category=category,
        meet_tier=meet_tier,
        before_year=target_year,
        division=division,
        equipment=equipment,
        region=region,
    )

    if history.empty:
        raise ValueError(
            "No real historical competition data is available for "
            f"{category}, division={division or 'any'}, "
            f"equipment={equipment or 'any'}, before {target_year}."
        )

    latest_year = int(
        pd.to_numeric(
            history["year"],
            errors="coerce",
        ).dropna().max()
    )

    latest = history[
        pd.to_numeric(
            history["year"],
            errors="coerce",
        ).eq(latest_year)
    ].copy()

    if latest.empty:
        return pd.DataFrame()

    result = _to_engine_columns(
        latest,
        requested_year=target_year,
        status=(
            "historical_real_benchmark"
            if scope == "exact division + equipment"
            else "historical_real_broader_benchmark"
        ),
        benchmark_year=latest_year,
    )
    result["scope_status"] = scope
    return result


# ============================================================
# HISTORICAL PODIUM
# ============================================================

def _get_historical_years(
    category: str,
    target_year: int,
    division: Optional[str],
    equipment: Optional[str],
) -> list[int]:
    """Return the latest real historical years before the target."""
    history, _ = _get_best_real_results(
        category=category,
        meet_tier="National",
        before_year=int(target_year),
        division=division,
        equipment=equipment,
    )

    if history.empty or "year" not in history.columns:
        return []

    years = pd.to_numeric(
        history["year"],
        errors="coerce",
    ).dropna()

    return sorted(
        {int(year) for year in years},
        reverse=True,
    )[:3]


def _get_year_podium(
    category: str,
    year: int,
    division: Optional[str],
    equipment: Optional[str],
    meet_tier: str = "National",
    competition: Optional[str] = None,
    region: Optional[str] = None,
) -> Optional[dict[str, float | int]]:
    """Get the strongest three real totals for one historical year."""
    results, _ = _get_best_real_results(
        category=category,
        meet_tier=meet_tier,
        year=int(year),
        division=division,
        equipment=equipment,
        competition=competition,
        region=region,
    )

    results = _competition_hint_match(
        results,
        meet_tier,
        competition,
    )

    if results.empty:
        return None

    if "total" in results.columns:
        results["total"] = pd.to_numeric(
            results["total"],
            errors="coerce",
        )

    results = results.dropna(
        subset=["total"]
    ).copy()

    if results.empty:
        return None

    # Prefer official place values when available. If places are
    # incomplete, sort by total as a deterministic fallback.
    if "place" in results.columns:
        results["_place"] = pd.to_numeric(
            results["place"],
            errors="coerce",
        )
    else:
        results["_place"] = pd.NA

    results = results.sort_values(
        ["_place", "total"],
        ascending=[True, False],
        na_position="last",
    ).reset_index(drop=True)

    # Keep one best valid total for each podium position.
    podium: dict[int, float] = {}

    for _, row in results.iterrows():
        place = row["_place"]

        if pd.notna(place):
            place_int = int(place)
            if place_int in (1, 2, 3) and place_int not in podium:
                podium[place_int] = float(row["total"])

        if len(podium) == 3:
            break

    # If official place numbers are incomplete, fill remaining slots
    # from the strongest real totals not already represented.
    if len(podium) < 3:
        totals = (
            pd.to_numeric(
                results["total"],
                errors="coerce",
            )
            .dropna()
            .sort_values(ascending=False)
            .tolist()
        )

        for total in totals:
            if len(podium) >= 3:
                break

            if total not in podium.values():
                missing_place = next(
                    place
                    for place in (1, 2, 3)
                    if place not in podium
                )
                podium[missing_place] = float(total)

    if not all(place in podium for place in (1, 2, 3)):
        return None

    return {
        "year": int(year),
        "gold": float(podium[1]),
        "silver": float(podium[2]),
        "bronze": float(podium[3]),
    }


# ============================================================
# PODIUM THRESHOLD
# ============================================================

def get_podium_threshold(
    category: str,
    meet_tier: str,
    target_year: int,
    competition: str | None = None,
    region: str | None = None,
    division: str | None = None,
    equipment: str | None = None,
) -> dict:
    """
    Calculate podium thresholds from real historical competition data.

    Historical target year:
        Uses actual real podium values when a complete podium exists.

    Future target year:
        Uses the latest three available real historical podiums and a
        transparent linear trend to estimate the target-year threshold.

    No synthetic competitors are generated.
    """
    _validate_category(category)
    _validate_tier(meet_tier)

    target_year = int(target_year)

    normalized_division = _normalise_division(division)
    normalized_equipment = _normalise_equipment(equipment)

    # ------------------------------------------------------------
    # Actual target-year podium if it exists.
    # ------------------------------------------------------------
    target_podium = _get_year_podium(
        category=category,
        year=target_year,
        division=normalized_division,
        equipment=normalized_equipment,
        meet_tier=meet_tier,
        competition=competition,
        region=region,
    )

    if target_podium is not None:
        bronze = float(target_podium["bronze"])

        return {
            "gold": round(float(target_podium["gold"]), 2),
            "silver": round(float(target_podium["silver"]), 2),
            "bronze": round(bronze, 2),
            "history": [target_podium],
            "trend": "flat",
            "target_year": target_year,
            "method": "Actual real historical podium for the target year.",
            "data_status": "historical_real",
            "benchmark_year": target_year,
        }

    # ------------------------------------------------------------
    # Future / unavailable target year:
    # build history from real data only.
    # ------------------------------------------------------------
    years = _get_historical_years(
        category=category,
        target_year=target_year,
        division=normalized_division,
        equipment=normalized_equipment,
    )

    history: list[dict[str, float | int]] = []

    for year in years:
        podium = _get_year_podium(
            category=category,
            year=year,
            division=normalized_division,
            equipment=normalized_equipment,
            meet_tier=meet_tier,
            competition=competition,
            region=region,
        )

        if podium is not None:
            history.append(podium)

    history = sorted(
        history,
        key=lambda item: int(item["year"]),
    )

    if not history:
        raise ValueError(
            "No real historical competition data is available for "
            f"{category}, division={normalized_division or 'any'}, "
            f"equipment={normalized_equipment or 'any'}, "
            f"before {target_year}."
        )

    # A single historical podium is still useful as a benchmark,
    # but cannot support a trend. Three years are preferred.
    if len(history) == 1:
        latest = history[-1]

        return {
            "gold": round(float(latest["gold"]), 2),
            "silver": round(float(latest["silver"]), 2),
            "bronze": round(float(latest["bronze"]), 2),
            "history": history,
            "trend": "flat",
            "target_year": target_year,
            "method": (
                "Latest available real historical podium; "
                "insufficient history for a trend projection."
            ),
            "data_status": "historical_real_benchmark",
            "benchmark_year": int(latest["year"]),
        }

    def forecast(position: str) -> float:
        x = pd.Series(
            [float(item["year"]) for item in history],
            dtype=float,
        )
        y = pd.Series(
            [float(item[position]) for item in history],
            dtype=float,
        )

        denominator = float(
            ((x - x.mean()) ** 2).sum()
        )

        if denominator == 0:
            return float(y.iloc[-1])

        slope = float(
            (
                (x - x.mean())
                * (y - y.mean())
            ).sum()
            / denominator
        )

        intercept = float(
            y.mean()
            - slope * x.mean()
        )

        return max(
            0.0,
            intercept + slope * target_year,
        )

    gold = forecast("gold")
    silver = forecast("silver")
    bronze = forecast("bronze")

    # Preserve podium ordering even if noisy historical data produces
    # a small regression crossing.
    gold = max(gold, silver, bronze)
    silver = min(gold, max(silver, bronze))
    bronze = min(silver, bronze)

    oldest_bronze = float(history[0]["bronze"])
    newest_bronze = float(history[-1]["bronze"])

    if newest_bronze > oldest_bronze:
        trend = "rising"
    elif newest_bronze < oldest_bronze:
        trend = "falling"
    else:
        trend = "flat"

    return {
        "gold": round(gold, 2),
        "silver": round(silver, 2),
        "bronze": round(bronze, 2),
        "history": history,
        "trend": trend,
        "target_year": target_year,
        "method": (
            "Linear trend over the latest available real "
            "historical podium years."
        ),
        "data_status": "future_real_data_projection",
        "benchmark_year": int(history[-1]["year"]),
    }


# ============================================================
# GAME PLAN — GAP ANALYSIS
# ============================================================

def get_gap_analysis(
    user_lifts: dict,
    threshold: dict,
    target_label: str = "Podium benchmark",
) -> dict:
    """
    Calculate transparent total and lift-level planning gaps.

    The allocation preserves the athlete's current contribution profile.
    These are planning heuristics, not ML predictions.
    """
    required_lifts = (
        "squat",
        "bench",
        "deadlift",
    )

    missing = [
        name
        for name in required_lifts
        if name not in user_lifts
    ]

    if missing:
        raise ValueError(
            "Missing lift values: "
            + ", ".join(missing)
        )

    lifts = {
        name: float(user_lifts[name])
        for name in required_lifts
    }

    if any(value < 0 for value in lifts.values()):
        raise ValueError(
            "Lift values cannot be negative."
        )

    current_total = sum(lifts.values())

    if "bronze" not in threshold:
        raise ValueError(
            "Podium threshold does not contain a bronze value."
        )

    target_benchmark = float(threshold["bronze"])

    if target_benchmark < 0:
        raise ValueError(
            "Target benchmark cannot be negative."
        )

    # Never create a planning target below the athlete's
    # current performance. If the current total already clears
    # bronze, the sensible baseline target is the athlete's
    # current total and every lift remains at its current value.
    target = max(
        target_benchmark,
        current_total,
    )

    total_gap = max(
        0.0,
        target_benchmark - current_total,
    )

    if current_total > 0:
        shares = {
            name: value / current_total
            for name, value in lifts.items()
        }
    else:
        shares = {
            name: 1 / 3
            for name in required_lifts
        }

    # Allocate only the required improvement on top of the
    # athlete's current lifts. This prevents the old bug where
    # an athlete with a 1000 kg total could receive "targets"
    # such as 318.8 / 106.2 / 283.3 kg.
    target_lifts = {
        name: lifts[name] + (total_gap * shares[name])
        for name in required_lifts
    }

    per_lift_gap = {
        name: max(
            0.0,
            target_lifts[name] - lifts[name],
        )
        for name in required_lifts
    }

    relative_weakness = {
        name: (1 / 3) - shares[name]
        for name in required_lifts
    }

    if total_gap <= 0:
        priority = "none"
    else:
        priority = max(
            per_lift_gap,
            key=per_lift_gap.get,
        )

    return {
        "current_total": round(current_total, 2),
        "target_total": round(target, 2),
        "total_gap_kg": round(total_gap, 2),
        "planning_profile": shares,
        "target_lifts": {
            name: round(value, 2)
            for name, value in target_lifts.items()
        },
        "per_lift_gap": {
            name: round(value, 2)
            for name, value in per_lift_gap.items()
        },
        "relative_weakness": {
            name: round(value, 4)
            for name, value in relative_weakness.items()
        },
        "priority_lift": priority,
        "planning_method": (
            f"Planning targets start from the athlete's current "
            f"Squat/Bench/Deadlift numbers and allocate only the "
            f"required improvement toward the {target_label.lower()} "
            f"using the current contribution profile. If the target is "
            f"already cleared, targets remain at the current lifts. "
            f"This is a transparent planning heuristic, not a prediction."
        ),
    }


# ============================================================
# WEIGHT-CLASS COMPARISON
# ============================================================

def get_category_recommendation(
    user_lifts: dict,
    current_bodyweight: float,
    target_year: int = 2027,
    meet_tier: str = "National",
    division: str = "Open",
    equipment: str = "CLASSIC",
) -> dict:
    """
    Compare the current and nearby men's weight classes using real
    historical podium thresholds.

    This is a threshold comparison only. It is not a recommendation
    to cut or gain bodyweight and does not estimate podium probability.
    Thresholds use the active competition plan context unless explicitly
    overridden by the optional arguments.
    """
    bodyweight = float(current_bodyweight)

    categories = [
        ("Men 53 kg", 53.0),
        ("Men 59 kg", 59.0),
        ("Men 66 kg", 66.0),
        ("Men 74 kg", 74.0),
        ("Men 83 kg", 83.0),
        ("Men 93 kg", 93.0),
        ("Men 105 kg", 105.0),
        ("Men 120 kg", 120.0),
        ("Men 120+ kg", float("inf")),
    ]

    current_index = len(categories) - 1

    for index, (_, limit) in enumerate(categories):
        if bodyweight <= limit:
            current_index = index
            break

    current_category = categories[current_index][0]

    candidate_indices = sorted(
        {
            index
            for index in (
                current_index - 1,
                current_index,
                current_index + 1,
            )
            if 0 <= index < len(categories)
        }
    )

    comparisons = []

    for index in candidate_indices:
        category = categories[index][0]

        try:
            threshold = get_podium_threshold(
                category,
                meet_tier,
                int(target_year),
                division=division,
                equipment=equipment,
            )
        except ValueError:
            continue

        comparisons.append(
            {
                "category": category,
                "bronze": float(threshold["bronze"]),
            }
        )

    if not comparisons:
        raise ValueError(
            "Unable to calculate weight-class comparison."
        )

    current_comparison = next(
        (
            item
            for item in comparisons
            if item["category"] == current_category
        ),
        None,
    )

    if current_comparison is None:
        raise ValueError(
            "Current category threshold could not be calculated."
        )

    current_bronze = float(
        current_comparison["bronze"]
    )

    comparison_category = min(
        comparisons,
        key=lambda item: item["bronze"],
    )

    recommended_category = comparison_category["category"]
    recommended_bronze = float(
        comparison_category["bronze"]
    )

    difference = (
        recommended_bronze
        - current_bronze
    )

    return {
        "current_category": current_category,
        "recommended_category": recommended_category,
        "podium_threshold_difference_kg": round(
            difference,
            2,
        ),
        "current_bronze_threshold": round(
            current_bronze,
            2,
        ),
        "recommended_bronze_threshold": round(
            recommended_bronze,
            2,
        ),
        "comparisons": [
            {
                "category": item["category"],
                "bronze": round(
                    item["bronze"],
                    2,
                ),
            }
            for item in comparisons
        ],
        "reason": (
            "Nearby weight classes are compared using their "
            "real-data podium thresholds."
        ),
    }
