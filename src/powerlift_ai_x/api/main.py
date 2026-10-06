from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from powerlift_ai_x.ml.model_service import (
    PowerLiftModelService,
)
from powerlift_ai_x.ml.temporal_features import (
    build_supervised_temporal_dataset,
    extract_production_features,
)


app = FastAPI(
    title="PowerLift-AI-X API",
    version="1.0.0",
    description="Powerlifting performance prediction API.",
)


# Load models once when the API starts.
model_service = PowerLiftModelService()


# ============================================================
# REQUEST MODELS
# ============================================================

class CompetitionRecord(BaseModel):
    """
    One historical competition record.
    """

    resolved_athlete_id: str

    year: int

    total: float | None = None

    best_squat: float | None = None
    best_bench: float | None = None
    best_deadlift: float | None = None

    bodyweight: float | None = None

    squat_1: float | None = None
    squat_2: float | None = None
    squat_3: float | None = None

    bench_1: float | None = None
    bench_2: float | None = None
    bench_3: float | None = None

    deadlift_1: float | None = None
    deadlift_2: float | None = None
    deadlift_3: float | None = None


class PredictionRequest(BaseModel):
    """
    Prediction request.

    history contains competitions strictly before the
    requested target year.
    """

    athlete_id: str

    target_year: int

    division: str

    weight_class: str

    equipment: str

    history: list[CompetitionRecord] = Field(
        min_length=1
    )


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health() -> dict[str, Any]:
    """
    Return API and model-service health.
    """

    return model_service.health()


# ============================================================
# PREDICTION
# ============================================================

@app.post("/predict")
def predict(
    request: PredictionRequest,
) -> dict[str, Any]:
    """
    Predict the athlete's next competition:

        squat
        bench
        deadlift
        total
    """

    # --------------------------------------------------------
    # Convert history to DataFrame
    # --------------------------------------------------------

    history_rows = [
        record.model_dump()
        for record in request.history
    ]

    history_df = pd.DataFrame(
        history_rows
    )

    # --------------------------------------------------------
    # Validate athlete identity
    # --------------------------------------------------------

    history_df[
        "athlete_id"
    ] = request.athlete_id

    # The temporal pipeline expects this canonical ID.
    history_df[
        "resolved_athlete_id"
    ] = history_df[
        "resolved_athlete_id"
    ].astype(str)

    # --------------------------------------------------------
    # Ensure historical competitions are before target
    # --------------------------------------------------------

    if (
        history_df["year"]
        >= request.target_year
    ).any():
        raise HTTPException(
            status_code=400,
            detail=(
                "All history competitions must occur "
                "strictly before target_year."
            ),
        )

    # --------------------------------------------------------
    # Build temporal dataset
    # --------------------------------------------------------

    try:
        temporal = (
            build_supervised_temporal_dataset(
                history_df
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if temporal.empty:
        raise HTTPException(
            status_code=400,
            detail=(
                "Insufficient historical data to "
                "generate temporal features."
            ),
        )

    # --------------------------------------------------------
    # Take the most recent historical competition
    # --------------------------------------------------------

    latest_history = (
        temporal
        .sort_values("year")
        .iloc[-1]
        .copy()
    )

    # --------------------------------------------------------
    # Build target feature row
    # --------------------------------------------------------

    target_row = {
        "year": request.target_year,
        "division": request.division,
        "weight_class": request.weight_class,
        "equipment": request.equipment,
    }

    for feature in [
        "previous_year_count",
        "previous_year",
        "years_since_previous",
        "previous_total",
        "previous_squat",
        "previous_bench",
        "previous_deadlift",
        "previous_bodyweight",
        "historical_mean_total",
        "historical_max_total",
        "historical_min_total",
        "historical_std_total",
        "historical_max_squat",
        "historical_max_bench",
        "historical_max_deadlift",
        "historical_mean_bodyweight",
        "previous_total_change",
        "previous_total_change_pct",
    ]:
        target_row[feature] = latest_history[
            feature
        ]

    X = pd.DataFrame(
        [target_row]
    )

    # --------------------------------------------------------
    # Extract exact 22-feature contract
    # --------------------------------------------------------

    X = extract_production_features(
        X
    )

    # --------------------------------------------------------
    # Predict
    # --------------------------------------------------------

    try:
        predictions = model_service.predict(
            X
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Prediction failed: {exc}"
            ),
        ) from exc

    row = predictions.iloc[0]

    return {
        "status": "ok",
        "athlete_id": request.athlete_id,
        "target_year": request.target_year,
        "predictions": {
            "future_best_squat": float(
                row["future_best_squat"]
            ),
            "future_best_bench": float(
                row["future_best_bench"]
            ),
            "future_best_deadlift": float(
                row["future_best_deadlift"]
            ),
            "future_total": float(
                row["future_total"]
            ),
        },
    }