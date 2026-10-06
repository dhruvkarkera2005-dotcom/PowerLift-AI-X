from powerlift_ai_x.identity.assignment import (
    make_resolved_athlete_id,
)


def test_name_and_dob_produce_deterministic_identity():
    first = make_resolved_athlete_id(
        athlete_name="PANNEERASELVAM S",
        date_of_birth="13-08-1991",
    )

    second = make_resolved_athlete_id(
        athlete_name="PANNEERASELVAM S",
        date_of_birth="13-08-1991",
    )

    assert first == second
    assert first.resolved_athlete_id.startswith("ATH-")
    assert first.confidence == "HIGH"


def test_different_dob_produces_different_identity():
    first = make_resolved_athlete_id(
        athlete_name="TEST ATHLETE",
        date_of_birth="10-05-1990",
    )

    second = make_resolved_athlete_id(
        athlete_name="TEST ATHLETE",
        date_of_birth="10-05-1991",
    )

    assert (
        first.resolved_athlete_id
        != second.resolved_athlete_id
    )


def test_same_name_different_dob_is_split():
    first = make_resolved_athlete_id(
        athlete_name="SAME NAME",
        date_of_birth="01-01-1990",
    )

    second = make_resolved_athlete_id(
        athlete_name="SAME NAME",
        date_of_birth="02-02-1990",
    )

    assert (
        first.resolved_athlete_id
        != second.resolved_athlete_id
    )


def test_missing_dob_keeps_candidate_identity():
    result = make_resolved_athlete_id(
        athlete_name="UNKNOWN ATHLETE",
        date_of_birth=None,
    )

    assert result.resolved_athlete_id.startswith(
        "ATH-"
    )

    assert result.confidence == "CANDIDATE"


def test_name_normalization_is_stable():
    first = make_resolved_athlete_id(
        athlete_name="  Test   Athlete  ",
        date_of_birth="10-05-1990",
    )

    second = make_resolved_athlete_id(
        athlete_name="TEST ATHLETE",
        date_of_birth="10-05-1990",
    )

    assert (
        first.resolved_athlete_id
        == second.resolved_athlete_id
    )
