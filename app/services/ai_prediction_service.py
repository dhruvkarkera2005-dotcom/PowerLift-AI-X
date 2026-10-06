from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.athlete_data_service import AthleteDataService
from powerlift_ai_x.ml.model_service import PowerLiftModelService
from powerlift_ai_x.ml.temporal_features import (
    build_athlete_year_table,
    build_supervised_temporal_dataset,
    extract_production_features,
)


class AIPredictionService:
    """
    Application service for production PowerLift-AI-X inference.

    The service reuses the same trained model and production feature
    contract as the API.

    Important:
    - If an athlete has 2+ historical years, the normal temporal
      supervised feature path is used.
    - If an athlete has exactly 1 historical year before the target
      year, a target-year feature row is bootstrapped from that real
      historical result. This allows the trained model to estimate
      what the athlete could total if they compete in the target year.
    - No prediction is generated when there is no historical result.
    """

    def __init__(
        self,
        athlete_data_service: AthleteDataService | None = None,
        model_service: PowerLiftModelService | None = None,
    ) -> None:

        self.athlete_data_service = (
            athlete_data_service
            if athlete_data_service is not None
            else AthleteDataService()
        )

        self.model_service = (
            model_service
            if model_service is not None
            else PowerLiftModelService()
        )

    # ========================================================
    # SINGLE-HISTORY TARGET ROW
    # ========================================================

    @staticmethod
    def _build_single_history_target_row(
        history: pd.DataFrame,
        *,
        target_year: int,
        division: str,
        weight_class: str,
        equipment: str,
    ) -> pd.DataFrame:
        """
        Build a production-compatible target row when only one
        historical athlete-year exists.

        The latest real result becomes the previous-performance
        context. Historical aggregates therefore equal that one
        real historical year. Change features are unavailable and
        are represented as zero, which is consistent with the
        absence of an earlier comparison year.
        """

        athlete_year = build_athlete_year_table(history)

        if athlete_year.empty:
            raise ValueError(
                "No usable athlete-year history exists."
            )

        latest = (
            athlete_year
            .sort_values("year", kind="stable")
            .iloc[-1]
        )

        previous_year = float(latest["year"])
        previous_total = float(latest["year_total_mean"])
        previous_squat = float(latest["year_best_squat"])
        previous_bench = float(latest["year_best_bench"])
        previous_deadlift = float(latest["year_best_deadlift"])
        previous_bodyweight = float(latest["year_bodyweight_mean"])

        target_row = {
            "year": int(target_year),
            "division": division,
            "weight_class": weight_class,
            "equipment": equipment,

            "previous_year_count": 1,
            "previous_year": previous_year,
            "years_since_previous": max(
                0.0,
                float(target_year) - previous_year,
            ),

            "previous_total": previous_total,
            "previous_squat": previous_squat,
            "previous_bench": previous_bench,
            "previous_deadlift": previous_deadlift,
            "previous_bodyweight": previous_bodyweight,

            "historical_mean_total": previous_total,
            "historical_max_total": float(latest["year_total_max"]),
            "historical_min_total": float(latest["year_total_min"]),
            "historical_std_total": 0.0,

            "historical_max_squat": previous_squat,
            "historical_max_bench": previous_bench,
            "historical_max_deadlift": previous_deadlift,

            "historical_mean_bodyweight": previous_bodyweight,

            # There is no second historical year, so a change from
            # an earlier year cannot be calculated.
            "previous_total_change": 0.0,
            "previous_total_change_pct": 0.0,
        }

        return pd.DataFrame([target_row])

    # ========================================================
    # PREDICT
    # ========================================================

    def predict(
        self,
        *,
        athlete_id: str,
        target_year: int,
        division: str,
        weight_class: str,
        equipment: str,
    ) -> dict[str, Any]:
        """
        Generate an AI prediction for an existing athlete.

        Historical records are restricted to years strictly before
        target_year.

        One historical year is now sufficient to produce a model
        estimate for the target year.
        """

        athlete_id = str(athlete_id).strip()

        if not athlete_id:
            raise ValueError(
                "athlete_id cannot be empty."
            )

        target_year = int(target_year)

        history = self.athlete_data_service.get_history(
            athlete_id,
            before_year=target_year,
        )

        if history.empty:
            raise ValueError(
                "No historical competition data exists before "
                f"target year {target_year} for athlete "
                f"{athlete_id}."
            )

        history = history.copy()

        history["resolved_athlete_id"] = (
            history["resolved_athlete_id"]
            .astype(str)
        )

        # ----------------------------------------------------
        # Normal temporal path for athletes with 2+ years
        # ----------------------------------------------------

        temporal = build_supervised_temporal_dataset(history)

        if not temporal.empty:
            latest_history = (
                temporal
                .sort_values(
                    ["year", "competition"],
                    kind="stable",
                )
                .iloc[-1]
                .copy()
            )

            target_row: dict[str, Any] = {
                "year": target_year,
                "division": division,
                "weight_class": weight_class,
                "equipment": equipment,
            }

            history_features = [
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
            ]

            for feature in history_features:
                target_row[feature] = latest_history[feature]

            target_df = pd.DataFrame([target_row])

        else:
            # ------------------------------------------------
            # One-year bootstrap path
            # ------------------------------------------------
            target_df = self._build_single_history_target_row(
                history,
                target_year=target_year,
                division=division,
                weight_class=weight_class,
                equipment=equipment,
            )

        # ----------------------------------------------------
        # Exact production feature contract
        # ----------------------------------------------------

        target_df = extract_production_features(
            target_df
        )

        # ----------------------------------------------------
        # Run trained models
        # ----------------------------------------------------

        predictions = self.model_service.predict(
            target_df
        )

        row = predictions.iloc[0]

        predicted_squat = float(
            row["future_best_squat"]
        )

        predicted_bench = float(
            row["future_best_bench"]
        )

        predicted_deadlift = float(
            row["future_best_deadlift"]
        )

        predicted_total = float(
            row["future_total"]
        )

        return {
            "status": "ok",
            "athlete_id": athlete_id,
            "target_year": target_year,
            "division": division,
            "weight_class": weight_class,
            "equipment": equipment,
            "predictions": {
                "future_best_squat": predicted_squat,
                "future_best_bench": predicted_bench,
                "future_best_deadlift": predicted_deadlift,
                "future_total": predicted_total,
            },
        }

    # ========================================================
    # HEALTH
    # ========================================================

    def health(self) -> dict[str, Any]:
        """Return model-service health information."""

        return dict(
            self.model_service.health()
        )
