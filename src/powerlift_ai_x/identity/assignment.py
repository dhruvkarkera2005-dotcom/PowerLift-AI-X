from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional


# ============================================================
# RESOLVED IDENTITY
# ============================================================

@dataclass(frozen=True)
class ResolvedIdentity:
    """
    Deterministic resolved identity for one athlete record.
    """

    resolved_athlete_id: str
    confidence: str


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_identity_text(
    value: Optional[str],
) -> Optional[str]:
    """
    Normalize optional identity text.
    """

    if value is None:
        return None

    value = " ".join(
        value.strip().split()
    ).upper()

    return value or None


# ============================================================
# RESOLVED ATHLETE ID
# ============================================================

def make_resolved_athlete_id(
    *,
    athlete_name: str,
    date_of_birth: Optional[str],
) -> ResolvedIdentity:
    """
    Generate a deterministic resolved athlete identity.

    Strong identity:
        normalized name + normalized DOB

    Fallback:
        candidate name-only identity when DOB is unavailable.
    """

    name = normalize_identity_text(
        athlete_name
    )

    if not name:
        raise ValueError(
            "athlete_name is required"
        )

    dob = normalize_identity_text(
        date_of_birth
    )

    if dob is not None:
        identity_key = (
            f"{name}|{dob}"
        )

        confidence = "HIGH"

    else:
        identity_key = name

        confidence = "CANDIDATE"

    digest = hashlib.sha256(
        identity_key.encode("utf-8")
    ).hexdigest()[:16]

    return ResolvedIdentity(
        resolved_athlete_id=f"ATH-{digest}",
        confidence=confidence,
    )
