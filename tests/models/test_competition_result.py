import pytest
from pydantic import ValidationError
from powerlift_ai_x.models import CompetitionResult, Equipment
from powerlift_ai_x.models import CompetitionResult


def test_valid_competition_result():
    result = CompetitionResult(
        athlete_id="ATH001",
        competition="Test Competition",
        year=2026,
        division="Men",
        weight_class="83 kg",
        equipment="CLASSIC",
        bodyweight=82.5,
        best_squat=200.0,
        best_bench=140.0,
        best_deadlift=240.0,
        total=580.0,
        place=1,
    )

    assert result.athlete_id == "ATH001"
    assert result.best_squat == 200.0
    assert result.best_bench == 140.0
    assert result.best_deadlift == 240.0
    assert result.total == 580.0
    assert result.place == 1


def test_optional_lift_values_can_be_missing():
    result = CompetitionResult(
        athlete_id="ATH002",
        competition="Test Competition",
        year=2026,
        division="Men",
        weight_class="74 kg",
        equipment="CLASSIC",
    )

    assert result.best_squat is None
    assert result.best_bench is None
    assert result.best_deadlift is None
    assert result.total is None
    assert result.place is None


def test_empty_athlete_id_is_rejected():
    with pytest.raises(ValidationError):
        CompetitionResult(
            athlete_id="",
            competition="Test Competition",
            year=2026,
            division="Men",
            weight_class="74 kg",
            equipment="CLASSIC",
        )


def test_empty_competition_is_rejected():
    with pytest.raises(ValidationError):
        CompetitionResult(
            athlete_id="ATH003",
            competition="",
            year=2026,
            division="Men",
            weight_class="74 kg",
            equipment="CLASSIC",
        )
def test_invalid_equipment_is_rejected():
    with pytest.raises(ValidationError):
        CompetitionResult(
            athlete_id="ATH004",
            competition="Test Competition",
            year=2026,
            division="Men",
            weight_class="83 kg",
            equipment="POWERLIFTING",
        )