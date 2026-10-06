from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class IdentityDecision(str, Enum):
    """
    Decision produced by the athlete identity resolver.
    """

    SAME = "SAME"
    SPLIT = "SPLIT"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class IdentityCandidate:
    """
    Identity information available for one competition result.
    """

    athlete_id: str
    date_of_birth: Optional[str]
    team: Optional[str]
    lot: Optional[str]
    bodyweight: Optional[float]
    division: str
    weight_class: str
    equipment: str


@dataclass(frozen=True)
class IdentityResolution:
    """
    Result of comparing two candidate records.
    """

    decision: IdentityDecision
    reason: str


def normalize_optional_text(
    value: Optional[str],
) -> Optional[str]:
    """
    Normalize optional identity metadata.
    """

    if value is None:
        return None

    value = value.strip()

    if not value:
        return None

    return value.upper()


def resolve_identity_pair(
    left: IdentityCandidate,
    right: IdentityCandidate,
) -> IdentityResolution:
    """
    Resolve whether two records with the same candidate
    athlete ID represent the same athlete.

    Conservative identity resolution rules:

    1. Different known DOBs -> SPLIT.
    2. Same known DOBs -> SAME.
    3. When DOB is unavailable:
       different weight classes within the same competition
       -> SPLIT.
    4. Otherwise -> UNRESOLVED.

    Weight class is used only as a strong contradiction
    inside an already detected collision group. An athlete
    may legitimately change weight class between different
    competitions.
    """

    left_dob = normalize_optional_text(
        left.date_of_birth
    )

    right_dob = normalize_optional_text(
        right.date_of_birth
    )

    # --------------------------------------------------------
    # Rule 1: Different known DOBs = different athletes.
    # --------------------------------------------------------

    if (
        left_dob is not None
        and right_dob is not None
        and left_dob != right_dob
    ):
        return IdentityResolution(
            decision=IdentityDecision.SPLIT,
            reason="DIFFERENT_DATE_OF_BIRTH",
        )

    # --------------------------------------------------------
    # Rule 2: Same known DOB = same athlete.
    # --------------------------------------------------------

    if (
        left_dob is not None
        and right_dob is not None
        and left_dob == right_dob
    ):
        return IdentityResolution(
            decision=IdentityDecision.SAME,
            reason="SAME_DATE_OF_BIRTH",
        )

    # --------------------------------------------------------
    # Rule 3: DOB unavailable.
    #
    # Different weight classes within the same collision
    # group are strong evidence that these are different
    # athletes.
    #
    # The collision resolver already groups records by:
    #
    #     athlete_id + year + competition
    #
    # Therefore this comparison is competition-local.
    # --------------------------------------------------------

    left_weight_class = normalize_optional_text(
        left.weight_class
    )

    right_weight_class = normalize_optional_text(
        right.weight_class
    )

    if (
        left_weight_class is not None
        and right_weight_class is not None
        and left_weight_class != right_weight_class
    ):
        return IdentityResolution(
            decision=IdentityDecision.SPLIT,
            reason="DIFFERENT_WEIGHT_CLASS_WITHOUT_DOB",
        )

    # --------------------------------------------------------
    # Rule 4: Insufficient evidence.
    #
    # Same weight class with missing DOB cannot safely
    # determine identity.
    # --------------------------------------------------------

    return IdentityResolution(
        decision=IdentityDecision.UNRESOLVED,
        reason="INSUFFICIENT_IDENTITY_METADATA",
    )