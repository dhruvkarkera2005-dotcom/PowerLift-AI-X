from __future__ import annotations

import pandas as pd


# ============================================================
# ATHLETE / COMPETITION CONFIGURATION
# ============================================================

WEIGHT_CLASSES = (
    "53 kg",
    "59 kg",
    "66 kg",
    "74 kg",
    "83 kg",
    "93 kg",
    "105 kg",
    "120 kg",
    "120+ kg",
)

DIVISIONS = (
    "Sub Junior",
    "Junior",
    "Open",
    "Master 1",
    "Master 2",
    "Master 3",
    "Master 4",
)

EQUIPMENT = (
    "CLASSIC",
    "EQUIPPED",
)


# ============================================================
# SUPPORTED FRONTEND COMPETITION TYPES
# ============================================================

# IMPORTANT:
# Only expose competition families currently supported by
# PowerLift AI-X data.
COMPETITION_TYPES = (
    "Nationals",
    "Regional",
)

REGIONS = (
    "India",
    "East India",
    "West India",
    "North India",
    "South India",
)


# ============================================================
# YEAR CONFIGURATION
# ============================================================

# Years for which the current frontend competition-history
# prototype contains observations.
HISTORICAL_YEARS = (
    2024,
    2025,
    2026,
)

# Years users may select as prediction/planning targets.
#
# These are intentionally separate from historical years.
PLANNING_YEARS = tuple(
    range(2026, 2036)
)

# Backward compatibility for existing engine/tests.
YEARS = HISTORICAL_YEARS


# ============================================================
# ENGINE COMPATIBILITY
# ============================================================

CATEGORIES = tuple(
    f"Men {weight_class}"
    for weight_class in WEIGHT_CLASSES
)

# Current statistical engine uses National as the competitive
# strength tier for the supported National/Regional prototype.
#
# Competition identity itself is preserved separately through
# competition_type, region and competition.
MEET_TIERS = (
    "State",
    "National",
    "International",
)


# ============================================================
# COMPETITION CATALOGUE
# ============================================================

# Do not add State or International competitions here until
# appropriate source data is available.
COMPETITIONS = (
    {
        "name": "National Powerlifting Championship",
        "competition_type": "Nationals",
        "region": "India",
        "tier": "National",
    },
    {
        "name": "East India Powerlifting Championship",
        "competition_type": "Regional",
        "region": "East India",
        "tier": "National",
    },
    {
        "name": "West India Powerlifting Championship",
        "competition_type": "Regional",
        "region": "West India",
        "tier": "National",
    },
    {
        "name": "North India Powerlifting Championship",
        "competition_type": "Regional",
        "region": "North India",
        "tier": "National",
    },
    {
        "name": "South India Powerlifting Championship",
        "competition_type": "Regional",
        "region": "South India",
        "tier": "National",
    },
)


# ============================================================
# SYNTHETIC DEVELOPMENT BASELINES
# ============================================================

def _category_base_total(
    category: str,
) -> float:
    """
    Return the synthetic competitive baseline for a category.

    These values exist only for frontend/engine development.
    They are not official qualifying standards or historical
    competition results.
    """

    bases = {
        "Men 53 kg": 350.0,
        "Men 59 kg": 410.0,
        "Men 66 kg": 500.0,
        "Men 74 kg": 575.0,
        "Men 83 kg": 650.0,
        "Men 93 kg": 725.0,
        "Men 105 kg": 800.0,
        "Men 120 kg": 850.0,
        "Men 120+ kg": 900.0,
    }

    try:
        return bases[category]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported category: {category}"
        ) from exc


def _tier_multiplier(
    meet_tier: str,
) -> float:
    """
    Return the synthetic competitive-strength multiplier.

    These multipliers are ONLY for synthetic engine testing.
    They are not official competition standards.
    """

    multipliers = {
        "State": 0.90,
        "National": 1.00,
        "International": 1.08,
    }

    try:
        return multipliers[meet_tier]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported meet tier: {meet_tier}"
        ) from exc


# ============================================================
# SYNTHETIC COMPETITION HISTORY
# ============================================================

def generate_competition_data() -> pd.DataFrame:
    """
    Generate deterministic synthetic competition history.

    This provider exists only while the production historical
    competition provider is being connected.

    IMPORTANT:
    The synthetic tier variants below are development fixtures
    used to test the competition engine across multiple levels.
    They are NOT real competitions and must never be presented
    as verified historical results.

    Columns:
        category
        meet_tier
        competition_type
        region
        competition
        name
        total_kg
        wilks_or_gl
        placing
        year
    """

    rows: list[dict[str, object]] = []

    competitors = (
        "Competitor A",
        "Competitor B",
        "Competitor C",
        "Competitor D",
        "Competitor E",
    )

    # Development-only competitive tiers.
    #
    # These are deliberately separate from COMPETITIONS because
    # they exist to test the engine's tier calculations rather
    # than to create user-facing competition choices.
    synthetic_tiers = (
        "State",
        "National",
        "International",
    )

    for category in CATEGORIES:
        base_total = _category_base_total(
            category
        )

        for competition_index, competition in enumerate(
            COMPETITIONS
        ):
            competition_type = str(
                competition["competition_type"]
            )

            region = str(
                competition["region"]
            )

            competition_name = str(
                competition["name"]
            )

            for tier_index, meet_tier in enumerate(
                synthetic_tiers
            ):
                tier_multiplier = _tier_multiplier(
                    meet_tier
                )

                for year_index, year in enumerate(
                    HISTORICAL_YEARS
                ):
                    # Deterministic year-over-year creep.
                    year_creep = (
                        year_index * 7.5
                    )

                    # Deterministic competition variation.
                    competition_adjustment = (
                        competition_index * 3.0
                    )

                    field_strength = (
                        base_total
                        * tier_multiplier
                        + year_creep
                        + competition_adjustment
                    )

                    # Small deterministic separation between
                    # synthetic competitive tiers.
                    tier_adjustment = (
                        tier_index * 2.5
                    )

                    field_strength += (
                        tier_adjustment
                    )

                    for placing, name in enumerate(
                        competitors,
                        start=1,
                    ):
                        placing_adjustment = (
                            (5 - placing)
                            * 17.5
                        )

                        total = (
                            field_strength
                            + placing_adjustment
                        )

                        gl_score = (
                            total
                            / base_total
                            * 100.0
                        )

                        rows.append(
                            {
                                "category": category,
                                "meet_tier": meet_tier,
                                "competition_type": (
                                    competition_type
                                ),
                                "region": region,
                                "competition": (
                                    competition_name
                                ),
                                "name": (
                                    f"{name} "
                                    f"{category.replace(' ', '_')}"
                                ),
                                "total_kg": round(
                                    total,
                                    1,
                                ),
                                "wilks_or_gl": round(
                                    gl_score,
                                    2,
                                ),
                                "placing": placing,
                                "year": year,
                            }
                        )

    return pd.DataFrame(
        rows
    )


# ============================================================
# CATALOGUE HELPERS
# ============================================================

def get_competition_catalogue() -> pd.DataFrame:
    """
    Return the supported competition catalogue.
    """

    return pd.DataFrame(
        COMPETITIONS
    ).copy()


def get_competitions(
    *,
    competition_type: str | None = None,
    region: str | None = None,
    year: int | None = None,
) -> pd.DataFrame:
    """
    Return supported competitions matching supplied filters.

    year is a planning attribute and does not imply historical
    results exist for that year.
    """

    df = get_competition_catalogue()

    if competition_type is not None:
        df = df[
            df["competition_type"]
            == competition_type
        ]

    if region is not None:
        df = df[
            df["region"]
            == region
        ]

    if year is not None:
        df = df.assign(
            year=year
        )

    return df.reset_index(
        drop=True
    )