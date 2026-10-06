from pathlib import Path

import pytest

from app.services.ai_prediction_service import AIPredictionService
from app.services.athlete_data_service import AthleteDataService


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "final"
    / "ml"
    / "powerlift_ai_x_ml_dataset.xlsx"
)


ATHLETE_ID = "ATH-0062b12dae143d50"
ATHLETE_NAME = "CHANDAN DAS"


@pytest.fixture(scope="module")
def athlete_service() -> AthleteDataService:
    return AthleteDataService(DATASET_PATH)


@pytest.fixture(scope="module")
def prediction_service(
    athlete_service: AthleteDataService,
) -> AIPredictionService:
    return AIPredictionService(
        athlete_data_service=athlete_service
    )


def test_prediction_service_health(
    prediction_service: AIPredictionService,
) -> None:
    health = prediction_service.health()

    assert health["status"] == "ok"


def test_prediction_requires_sufficient_history(
    prediction_service: AIPredictionService,
) -> None:
    with pytest.raises(
        ValueError,
        match="No historical competition data",
    ):
        prediction_service.predict(
            athlete_id=ATHLETE_ID,
            target_year=2018,
            division="Men",
            weight_class="83",
            equipment="Classic",
        )


def test_prediction_rejects_unknown_athlete(
    prediction_service: AIPredictionService,
) -> None:
    with pytest.raises(KeyError, match="Athlete not found"):
        prediction_service.predict(
            athlete_id="ATH-does-not-exist",
            target_year=2027,
            division="Men",
            weight_class="83",
            equipment="Classic",
        )


def test_real_prediction_returns_expected_structure(
    prediction_service: AIPredictionService,
) -> None:
    result = prediction_service.predict(
        athlete_id=ATHLETE_ID,
        target_year=2024,
        division="Men",
        weight_class="83",
        equipment="Classic",
    )

    assert result["status"] == "ok"
    assert result["athlete_id"] == ATHLETE_ID
    assert result["target_year"] == 2024
    assert result["division"] == "Men"
    assert result["weight_class"] == "83"
    assert result["equipment"] == "Classic"

    assert set(result["predictions"]) == {
        "future_best_squat",
        "future_best_bench",
        "future_best_deadlift",
        "future_total",
    }


def test_real_prediction_values_are_numeric(
    prediction_service: AIPredictionService,
) -> None:
    result = prediction_service.predict(
        athlete_id=ATHLETE_ID,
        target_year=2024,
        division="Men",
        weight_class="83",
        equipment="Classic",
    )

    predictions = result["predictions"]

    for value in predictions.values():
        assert isinstance(value, float)
        assert value >= 0


def test_prediction_uses_target_category_context(
    prediction_service: AIPredictionService,
) -> None:
    result = prediction_service.predict(
        athlete_id=ATHLETE_ID,
        target_year=2024,
        division="Men",
        weight_class="93",
        equipment="Classic",
    )

    assert result["division"] == "Men"
    assert result["weight_class"] == "93"
    assert result["equipment"] == "Classic"

    predictions = result["predictions"]

    assert isinstance(
        predictions["future_best_squat"],
        float,
    )
    assert isinstance(
        predictions["future_best_bench"],
        float,
    )
    assert isinstance(
        predictions["future_best_deadlift"],
        float,
    )
    assert isinstance(
        predictions["future_total"],
        float,
    )