from app.services.performance_service import PerformanceService


KNOWN_ATHLETE_ID = "ATH-3329e53259abce06"


def test_get_latest_performance_snapshot_returns_real_record():
    service = PerformanceService()

    snapshot = service.get_latest_performance_snapshot(KNOWN_ATHLETE_ID)

    assert snapshot["athlete_id"] == KNOWN_ATHLETE_ID
    assert snapshot["athlete_name"] == "PANNEERASELVAM S"

    assert snapshot["squat"] == 200.0
    assert snapshot["bench"] == 120.0
    assert snapshot["deadlift"] == 232.5
    assert snapshot["total"] == 552.5
    assert snapshot["bodyweight"] == 58.8

    assert snapshot["source"] == "competition"
    assert snapshot["competition"] == (
        "National Classic Powerlifting Championship 2019"
    )
    assert snapshot["year"] == 2019


def test_latest_performance_snapshot_total_matches_lifts():
    service = PerformanceService()

    snapshot = service.get_latest_performance_snapshot(KNOWN_ATHLETE_ID)

    calculated_total = (
        snapshot["squat"]
        + snapshot["bench"]
        + snapshot["deadlift"]
    )

    assert snapshot["total"] == calculated_total


def test_unknown_athlete_raises_error():
    service = PerformanceService()

    try:
        service.get_latest_performance_snapshot("ATH-DOES-NOT-EXIST")
    except ValueError as exc:
        assert "No prediction-eligible performance record found" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown athlete")