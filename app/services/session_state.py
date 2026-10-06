from __future__ import annotations

from typing import Any

import streamlit as st


DEFAULT_STATE: dict[str, Any] = {
    # ---------------------------------------------------------
    # Competition plan
    # ---------------------------------------------------------
    "planned_meet": None,
    "planned_category": None,
    "planned_weight_class": None,
    "planned_goal": None,
    "planned_region": None,
    "planned_division": None,
    "planned_equipment": None,
    "planned_target_year": None,

    # ---------------------------------------------------------
    # Legacy athlete-selection state
    # Kept temporarily for compatibility with existing services.
    # The new user workflow does NOT depend on this.
    # ---------------------------------------------------------
    "selected_athlete_id": None,
    "selected_athlete_name": None,

    # ---------------------------------------------------------
    # User performance
    # ---------------------------------------------------------
    "performance_athlete_id": None,
    "performance_name": None,
    "performance_squat": None,
    "performance_bench": None,
    "performance_deadlift": None,
    "performance_bodyweight": None,
    "performance_source": None,
    "performance_competition": None,
    "performance_year": None,

    # ---------------------------------------------------------
    # AI prediction
    #
    # Stores the latest successful PowerLift-AI-X prediction
    # so that Competition Outlook and Game Plan can consume
    # the same prediction instead of generating/holding it
    # locally inside one page.
    # ---------------------------------------------------------
    "ai_prediction": None,
    "ai_prediction_athlete_id": None,
    "ai_prediction_target_year": None,
    "ai_prediction_status": None,
    "ai_prediction_error": None,

    # ---------------------------------------------------------
    # Competition Outlook handoff
    #
    # Stores the exact field/benchmark snapshot produced by
    # Competition Outlook so Game Plan can consume the same
    # competitive context instead of independently rebuilding it.
    # ---------------------------------------------------------
    "competition_outlook": None,
}


def initialize_session_state() -> None:
    """Initialize application session-state keys."""
    for key, value in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================
# COMPETITION PLAN
# =============================================================

def set_planned_competition(
    *,
    meet: dict[str, Any],
    category: str,
    weight_class: str,
    goal: str,
    region: str,
    division: str,
    equipment: str,
) -> None:
    """Store the user's planned competition."""
    st.session_state.planned_meet = meet
    st.session_state.planned_category = category
    st.session_state.planned_weight_class = weight_class
    st.session_state.planned_goal = goal
    st.session_state.planned_region = region
    st.session_state.planned_division = division
    st.session_state.planned_equipment = equipment
    st.session_state.planned_target_year = meet.get("year")

    # The Outlook snapshot belongs to the exact saved plan.
    clear_competition_outlook()


def get_planned_competition() -> dict[str, Any] | None:
    """Return the currently planned competition."""
    meet = st.session_state.get("planned_meet")

    if meet is None:
        return None

    return {
        "meet": meet,
        "category": st.session_state.get("planned_category"),
        "weight_class": st.session_state.get("planned_weight_class"),
        "goal": st.session_state.get("planned_goal"),
        "region": st.session_state.get("planned_region"),
        "division": st.session_state.get("planned_division"),
        "equipment": st.session_state.get("planned_equipment"),
        "target_year": st.session_state.get("planned_target_year"),
    }


# =============================================================
# LEGACY ATHLETE SELECTION
# =============================================================

def set_selected_athlete(
    athlete_id: str,
    athlete_name: str,
) -> None:
    """
    Store the currently selected historical athlete.

    This is retained for compatibility with existing backend
    services. The new frontend workflow uses manual My Performance
    data instead of requiring an athlete selection.
    """
    previous_athlete_id = st.session_state.get("selected_athlete_id")

    if (
        previous_athlete_id is not None
        and str(previous_athlete_id) != str(athlete_id)
    ):
        clear_performance_snapshot()

    st.session_state.selected_athlete_id = str(athlete_id)
    st.session_state.selected_athlete_name = str(athlete_name)


def get_selected_athlete() -> dict[str, str] | None:
    """Return the currently selected historical athlete, if one exists."""
    athlete_id = st.session_state.get("selected_athlete_id")
    athlete_name = st.session_state.get("selected_athlete_name")

    if not athlete_id:
        return None

    return {
        "resolved_athlete_id": str(athlete_id),
        "athlete_name": str(athlete_name or ""),
    }


def clear_selected_athlete() -> None:
    """Clear the selected athlete and its performance snapshot."""
    st.session_state.pop("selected_athlete_id", None)
    st.session_state.pop("selected_athlete_name", None)

    clear_performance_snapshot()


# =============================================================
# USER PERFORMANCE
# =============================================================

def set_performance_snapshot(
    *,
    athlete_id: str,
    name: str,
    squat: float,
    bench: float,
    deadlift: float,
    bodyweight: float,
    source: str,
    competition: str | None = None,
    year: int | None = None,
) -> None:
    """
    Store the user's current performance snapshot.

    The frontend can use athlete_id='USER-INPUT' when the
    performance has been entered manually.
    """
    st.session_state.performance_athlete_id = str(athlete_id)
    st.session_state.performance_name = str(name).strip()

    st.session_state.performance_squat = float(squat)
    st.session_state.performance_bench = float(bench)
    st.session_state.performance_deadlift = float(deadlift)
    st.session_state.performance_bodyweight = float(bodyweight)

    st.session_state.performance_source = str(source)
    st.session_state.performance_competition = competition

    st.session_state.performance_year = (
        int(year) if year is not None else None
    )

    # A changed personal baseline changes rank/gap context.
    clear_competition_outlook()


def set_performance_snapshot_from_service(
    snapshot: dict[str, Any],
) -> None:
    """
    Store a PerformanceService snapshot in session state.

    Kept for compatibility with the existing real-athlete
    performance service.
    """
    set_performance_snapshot(
        athlete_id=snapshot["athlete_id"],
        name=snapshot.get(
            "athlete_name",
            snapshot.get("name", ""),
        ),
        squat=snapshot["squat"],
        bench=snapshot["bench"],
        deadlift=snapshot["deadlift"],
        bodyweight=snapshot["bodyweight"],
        source=snapshot["source"],
        competition=snapshot.get("competition"),
        year=snapshot.get("year"),
    )


def get_performance_snapshot() -> dict[str, Any] | None:
    """
    Return the current performance snapshot.

    A snapshot is considered valid when Squat, Bench,
    Deadlift and Bodyweight are all present.
    """
    values = (
        st.session_state.get("performance_squat"),
        st.session_state.get("performance_bench"),
        st.session_state.get("performance_deadlift"),
        st.session_state.get("performance_bodyweight"),
    )

    if any(value is None for value in values):
        return None

    squat = float(values[0])
    bench = float(values[1])
    deadlift = float(values[2])
    bodyweight = float(values[3])

    return {
        "athlete_id": st.session_state.get("performance_athlete_id"),
        "name": st.session_state.get("performance_name"),
        "squat": squat,
        "bench": bench,
        "deadlift": deadlift,
        "bodyweight": bodyweight,
        "total": squat + bench + deadlift,
        "source": st.session_state.get("performance_source"),
        "competition": st.session_state.get("performance_competition"),
        "year": st.session_state.get("performance_year"),
    }


def clear_performance_snapshot() -> None:
    """Clear the current performance snapshot."""
    st.session_state.performance_athlete_id = None
    st.session_state.performance_name = None

    st.session_state.performance_squat = None
    st.session_state.performance_bench = None
    st.session_state.performance_deadlift = None
    st.session_state.performance_bodyweight = None

    st.session_state.performance_source = None
    st.session_state.performance_competition = None
    st.session_state.performance_year = None


# =============================================================
# COMPETITION OUTLOOK HANDOFF
# =============================================================

def set_competition_outlook(
    *,
    snapshot: dict[str, Any],
) -> None:
    """Store the exact Competition Outlook field/benchmark snapshot."""
    st.session_state.competition_outlook = snapshot


def get_competition_outlook() -> dict[str, Any] | None:
    """Return the latest Competition Outlook snapshot, if available."""
    snapshot = st.session_state.get("competition_outlook")

    if not isinstance(snapshot, dict):
        return None

    return snapshot


def clear_competition_outlook() -> None:
    """Clear the Outlook snapshot when its source context changes."""
    st.session_state.competition_outlook = None


# =============================================================
# AI PREDICTION
# =============================================================

def set_ai_prediction(
    *,
    prediction: dict[str, Any],
    athlete_id: str,
    target_year: int,
) -> None:
    """
    Store a successful AI prediction in session state.

    The complete prediction response is retained so downstream
    pages can consume the exact same model output.
    """
    st.session_state.ai_prediction = prediction
    st.session_state.ai_prediction_athlete_id = str(athlete_id)
    st.session_state.ai_prediction_target_year = int(target_year)
    st.session_state.ai_prediction_status = "ok"
    st.session_state.ai_prediction_error = None


def get_ai_prediction() -> dict[str, Any] | None:
    """
    Return the latest successful AI prediction.

    Returns None when no successful prediction is currently stored.
    """
    prediction = st.session_state.get("ai_prediction")

    if prediction is None:
        return None

    if st.session_state.get("ai_prediction_status") != "ok":
        return None

    return prediction


def set_ai_prediction_error(
    error: str,
    *,
    athlete_id: str | None = None,
    target_year: int | None = None,
) -> None:
    """
    Store an AI prediction failure without pretending that a
    prediction was generated.
    """
    st.session_state.ai_prediction = None

    st.session_state.ai_prediction_athlete_id = (
        str(athlete_id)
        if athlete_id is not None
        else None
    )

    st.session_state.ai_prediction_target_year = (
        int(target_year)
        if target_year is not None
        else None
    )

    st.session_state.ai_prediction_status = "error"
    st.session_state.ai_prediction_error = str(error)


def get_ai_prediction_status() -> str | None:
    """Return the current AI prediction status."""
    return st.session_state.get("ai_prediction_status")


def get_ai_prediction_error() -> str | None:
    """Return the latest AI prediction error, if any."""
    return st.session_state.get("ai_prediction_error")


def clear_ai_prediction() -> None:
    """Clear all stored AI prediction state."""
    st.session_state.ai_prediction = None
    st.session_state.ai_prediction_athlete_id = None
    st.session_state.ai_prediction_target_year = None
    st.session_state.ai_prediction_status = None
    st.session_state.ai_prediction_error = None