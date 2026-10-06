from __future__ import annotations

from typing import Any

from app.services.performance_service import PerformanceService
from app.services.session_state import set_performance_snapshot_from_service


class PerformanceStateService:
    """Coordinate real athlete performance data with application state."""

    def __init__(
        self,
        performance_service: PerformanceService | None = None,
    ) -> None:
        self.performance_service = (
            performance_service
            if performance_service is not None
            else PerformanceService()
        )

    def load_athlete_performance(
        self,
        athlete_id: str,
    ) -> dict[str, Any]:
        """Load an athlete's real performance and store it in session state."""

        snapshot = (
            self.performance_service
            .get_latest_performance_snapshot(athlete_id)
        )

        set_performance_snapshot_from_service(snapshot)

        return snapshot