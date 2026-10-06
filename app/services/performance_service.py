from __future__ import annotations

from typing import Any

from app.services.athlete_data_service import AthleteDataService


class PerformanceService:
    """Application service for loading an athlete's real performance snapshot."""

    def __init__(
        self,
        athlete_data_service: AthleteDataService | None = None,
    ) -> None:
        self.athlete_data_service = (
            athlete_data_service
            if athlete_data_service is not None
            else AthleteDataService()
        )

    def get_latest_performance_snapshot(
        self,
        athlete_id: str,
    ) -> dict[str, Any]:
        """Return the latest ML-eligible real competition performance."""

        try:
            record = self.athlete_data_service.get_latest_record(athlete_id)
        except KeyError as exc:
            raise ValueError(
                "No prediction-eligible performance record found "
                f"for athlete: {athlete_id}"
            ) from exc

        if record is None:
            raise ValueError(
                "No prediction-eligible performance record found "
                f"for athlete: {athlete_id}"
            )

        required_fields = (
            "athlete_name",
            "best_squat",
            "best_bench",
            "best_deadlift",
            "bodyweight",
            "total",
            "competition",
            "year",
        )

        missing_fields = [
            field
            for field in required_fields
            if record.get(field) is None
        ]

        if missing_fields:
            raise ValueError(
                "Latest performance record is missing required fields: "
                + ", ".join(missing_fields)
            )

        return {
            "athlete_id": athlete_id,
            "athlete_name": record["athlete_name"],
            "squat": float(record["best_squat"]),
            "bench": float(record["best_bench"]),
            "deadlift": float(record["best_deadlift"]),
            "bodyweight": float(record["bodyweight"]),
            "total": float(record["total"]),
            "source": "competition",
            "competition": record["competition"],
            "year": int(record["year"]),
        }