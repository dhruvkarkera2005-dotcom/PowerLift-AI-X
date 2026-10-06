from pathlib import Path

from powerlift_ai_x.identity.applier import (
    apply_identity_resolution,
    make_resolved_athlete_id,
)


def test_resolved_id_is_deterministic():
    first = make_resolved_athlete_id(
        "ATH-test",
        "22-09-1996",
    )

    second = make_resolved_athlete_id(
        "ATH-test",
        "22-09-1996",
    )

    assert first == second
    assert first.startswith("ATHR-")


def test_different_dobs_produce_different_resolved_ids():
    first = make_resolved_athlete_id(
        "ATH-test",
        "22-09-1996",
    )

    second = make_resolved_athlete_id(
        "ATH-test",
        "23-09-1996",
    )

    assert first != second


def test_same_collision_group_is_resolved_same():
    record = {
        "athlete_id": "ATH-test",
        "year": 2020,
        "competition": "TEST",
        "date_of_birth": "22-09-1996",
        "bodyweight": 74.0,
    }

    resolution = {
        "classification": "SAME",
    }

    result = apply_identity_resolution(
        record,
        resolution,
    )

    assert result["athlete_id"] == "ATH-test"

    assert result["resolved_athlete_id"].startswith(
        "ATHR-"
    )

    assert result["identity_confidence"] == (
        "RESOLVED_SAME"
    )


def test_split_collision_group_uses_dob():
    left = {
        "athlete_id": "ATH-test",
        "year": 2020,
        "competition": "TEST",
        "date_of_birth": "22-09-1996",
    }

    right = {
        "athlete_id": "ATH-test",
        "year": 2020,
        "competition": "TEST",
        "date_of_birth": "23-09-1996",
    }

    resolution = {
        "classification": "SPLIT",
    }

    left_result = apply_identity_resolution(
        left,
        resolution,
    )

    right_result = apply_identity_resolution(
        right,
        resolution,
    )

    assert (
        left_result["resolved_athlete_id"]
        != right_result["resolved_athlete_id"]
    )

    assert left_result["identity_confidence"] == (
        "RESOLVED_SPLIT"
    )

    assert right_result["identity_confidence"] == (
        "RESOLVED_SPLIT"
    )


def test_unresolved_identity_does_not_guess():
    record = {
        "athlete_id": "ATH-test",
        "year": 2025,
        "competition": "TEST",
        "date_of_birth": None,
    }

    resolution = {
        "classification": "UNRESOLVED",
    }

    result = apply_identity_resolution(
        record,
        resolution,
    )

    assert result["resolved_athlete_id"] is None

    assert result["identity_confidence"] == (
        "UNRESOLVED"
    )


def test_unique_candidate_keeps_original_identity():
    record = {
        "athlete_id": "ATH-test",
        "year": 2024,
        "competition": "TEST",
        "date_of_birth": "10-05-1995",
    }

    result = apply_identity_resolution(
        record,
        None,
    )

    assert result["resolved_athlete_id"] == (
        "ATH-test"
    )

    assert result["identity_confidence"] == (
        "UNIQUE_CANDIDATE"
    )