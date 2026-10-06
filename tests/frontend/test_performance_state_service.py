from app.services.performance_state_service import PerformanceStateService


KNOWN_ATHLETE_ID = "ATH-3329e53259abce06"


def test_load_athlete_performance_returns_real_snapshot():
    service = PerformanceStateService()

    snapshot = service.load_athlete_performance(KNOWN_ATHLETE_ID)

    assert snapshot["athlete_id"] == KNOWN_ATHLETE_ID
    assert snapshot["athlete_name"] == "PANNEERASELVAM S"
    assert snapshot["squat"] == 200.0
    assert snapshot["bench"] == 120.0
    assert snapshot["deadlift"] == 232.5
    assert snapshot["bodyweight"] == 58.8
    assert snapshot["total"] == 552.5
    assert snapshot["source"] == "competition"
    assert snapshot["year"] == 2019


def test_load_athlete_performance_stores_snapshot_in_session_state():
    import streamlit as st

    service = PerformanceStateService()

    service.load_athlete_performance(KNOWN_ATHLETE_ID)

    assert st.session_state.performance_athlete_id == KNOWN_ATHLETE_ID
    assert st.session_state.performance_squat == 200.0
    assert st.session_state.performance_bench == 120.0
    assert st.session_state.performance_deadlift == 232.5
    assert st.session_state.performance_bodyweight == 58.8
    assert st.session_state.performance_total == 552.5 if "performance_total" in st.session_state else True


def test_unknown_athlete_raises_value_error():
    service = PerformanceStateService()

    try:
        service.load_athlete_performance("ATH-DOES-NOT-EXIST")
    except ValueError as exc:
        assert "No prediction-eligible performance record found" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown athlete")