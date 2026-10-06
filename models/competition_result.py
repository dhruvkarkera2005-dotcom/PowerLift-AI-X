from typing import Optional

from pydantic import BaseModel, Field


class CompetitionResult(BaseModel):
    """
    Canonical representation of one athlete's competition result.

    All source-specific PDF formats must eventually be normalized
    into this structure.
    """

    athlete_id: str = Field(min_length=1)

    competition: str = Field(min_length=1)
    year: int

    division: str = Field(min_length=1)
    weight_class: str = Field(min_length=1)
    equipment: str = Field(min_length=1)

    bodyweight: Optional[float] = None

    best_squat: Optional[float] = None
    best_bench: Optional[float] = None
    best_deadlift: Optional[float] = None

    total: Optional[float] = None
    place: Optional[int] = None