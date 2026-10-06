from __future__ import annotations

from typing import Any

import streamlit as st


DEFAULT_STATE: dict[str, Any] = {
    "planned_meet": None,
    "planned_category": None,
    "planned_goal": None,
    "planned_region": None,
    "planned_division": None,
    "planned_equipment": None,
    "planned_target_year": None,

    "selected_athlete_id": None,
    "selected_athlete_name": None,

    "performance_athlete_id": None,
    "performance_squat": None,
    "performance_bench": None,
    "performance_deadlift": None,
    "performance_bodyweight": None,
    "performance_source": None,
    "performance_competition": None,
    "performance_year": None,
}


def initialize_session_state() -> None:
    """Initialize missing application state values."""

    for key, value in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_planned_competition(
    *,
    meet: dict[str, Any],
    category: str,
    goal: str,
    region: str,
    division: str,
    equipment: str,
) -> None:
    """Store the active competition plan."""

    st.session_state.planned_meet = meet
    st.session_state.planned_category = category
    st.session_state.planned_goal = goal
    st.session_state.planned_region = region
    st.session_state.planned_division = division
    st.session_state.planned_equipment = equipment
    st.session_state.planned_target_year = meet.get("year")


def get_planned_competition() -> dict[str, Any] | None:
    """Return the active competition plan."""

    meet = st.session_state.get("planned_meet")

    if meet is None:
        return None

    return {
        "meet": meet,
        "category": st.session_state.get("planned_category"),
        "goal": st.session_state.get("planned_goal"),
        "region": st.session_state.get("planned_region"),
        "division": st.session_state.get("planned_division"),
        "equipment": st.session_state.get("planned_equipment"),
        "target_year": st.session_state.get("planned_target_year"),
    }


def set_selected_athlete(
    athlete_id: str,
    athlete_name: str,
) -> None:
    """Store the currently selected athlete."""

    st.session_state["selected_athlete_id"] = str(athlete_id)
    st.session_state["selected_athlete_name"] = str(athlete_name)


def get_selected_athlete() -> dict[str, str] | None:
    """Return the currently selected athlete."""

    athlete_id = st.session_state.get("selected_athlete_id")
    athlete_name = st.session_state.get("selected_athlete_name")

    if not athlete_id:
        return None

    return {
        "resolved_athlete_id": str(athlete_id),
        "athlete_name": str(athlete_name or ""),
    }


def clear_selected_athlete() -> None:
    """Clear the selected athlete."""

    st.session_state.pop("selected_athlete_id", None)
    st.session_state.pop("selected_athlete_name", None)

    clear_performance_snapshot()


def set_performance_snapshot(
    *,
    athlete_id: str,
    squat: float,
    bench: float,
    deadlift: float,
    bodyweight: float,
    source: str,
    competition: str | None = None,
    year: int | None = None,
) -> None:
    """Store a performance snapshot belonging to a specific athlete."""

    st.session_state.performance_athlete_id = str(athlete_id)
    st.session_state.performance_squat = float(squat)
    st.session_state.performance_bench = float(bench)
    st.session_state.performance_deadlift = float(deadlift)
    st.session_state.performance_bodyweight = float(bodyweight)

    st.session_state.performance_source = str(source)
    st.session_state.performance_competition = (
        str(competition) if competition is not None else None
    )
    st.session_state.performance_year = (
        int(year) if year is not None else None
    )


def get_performance_snapshot() -> dict[str, Any] | None:
    """Return the performance snapshot when all required values exist."""

    values = (
        st.session_state.get("performance_athlete_id"),
        st.session_state.get("performance_squat"),
        st.session_state.get("performance_bench"),
        st.session_state.get("performance_deadlift"),
        st.session_state.get("performance_bodyweight"),
        st.session_state.get("performance_source"),
    )

    if any(value is None for value in values):
        return None

    return {
        "athlete_id": str(values[0]),
        "squat": float(values[1]),
        "bench": float(values[2]),
        "deadlift": float(values[3]),
        "bodyweight": float(values[4]),
        "source": str(values[5]),
        "competition": st.session_state.get(
            "performance_competition"
        ),
        "year": st.session_state.get(
            "performance_year"
        ),
    }


def clear_performance_snapshot() -> None:
    """Clear the stored performance snapshot."""

    st.session_state.performance_athlete_id = None
    st.session_state.performance_squat = None
    st.session_state.performance_bench = None
    st.session_state.performance_deadlift = None
    st.session_state.performance_bodyweight = None
    st.session_state.performance_source = None
    st.session_state.performance_competition = None
    st.session_state.performance_year = None