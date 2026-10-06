from app.services import session_state


def test_selected_athlete_can_be_stored_and_retrieved() -> None:
    session_state.set_selected_athlete(
        "ATH-6ec70392619dedd1",
        "PANNEERASELVAM S",
    )

    selected = session_state.get_selected_athlete()

    assert selected == {
        "resolved_athlete_id": "ATH-6ec70392619dedd1",
        "athlete_name": "PANNEERASELVAM S",
    }


def test_selected_athlete_can_be_cleared() -> None:
    session_state.set_selected_athlete(
        "ATH-6ec70392619dedd1",
        "PANNEERASELVAM S",
    )

    session_state.clear_selected_athlete()

    assert session_state.get_selected_athlete() is None


def test_no_selected_athlete_returns_none() -> None:
    session_state.clear_selected_athlete()

    assert session_state.get_selected_athlete() is None