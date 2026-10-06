from typing import Optional

from pydantic import BaseModel, Field

from powerlift_ai_x.models.enums import Equipment


class CompetitionResult(BaseModel):
    """
    Canonical representation of one athlete's
    complete powerlifting competition result.

    Raw attempts are preserved so that extraction
    and validation can be performed later.

    Identity fields:
        athlete_id:
            Original deterministic candidate ID generated
            from normalized athlete name.

        resolved_athlete_id:
            Deterministic identity ID generated from stronger
            identity evidence when available.

        identity_confidence:
            Confidence level of the resolved identity.
    """

    athlete_id: str = Field(min_length=1)
    athlete_name: Optional[str] = None

    resolved_athlete_id: Optional[str] = None

    identity_confidence: str = "CANDIDATE"

    competition: str = Field(min_length=1)
    year: int

    division: str = Field(min_length=1)
    weight_class: str = Field(min_length=1)
    equipment: Equipment

    date_of_birth: Optional[str] = None
    team: Optional[str] = None
    lot: Optional[str] = None

    bodyweight: Optional[float] = None

    squat_1: Optional[float] = None
    squat_2: Optional[float] = None
    squat_3: Optional[float] = None
    best_squat: Optional[float] = None

    bench_1: Optional[float] = None
    bench_2: Optional[float] = None
    bench_3: Optional[float] = None
    best_bench: Optional[float] = None

    deadlift_1: Optional[float] = None
    deadlift_2: Optional[float] = None
    deadlift_3: Optional[float] = None
    best_deadlift: Optional[float] = None

    total: Optional[float] = None
    place: Optional[int] = None