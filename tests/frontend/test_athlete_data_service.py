from pathlib import Path

import pandas as pd
import pytest

from app.services.athlete_data_service import AthleteDataService


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "final"
    / "ml"
    / "powerlift_ai_x_ml_dataset.xlsx"
)


@pytest.fixture(scope="module")
def service() -> AthleteDataService:
    return AthleteDataService(DATASET_PATH)


def test_dataset_loads(service: AthleteDataService) -> None:
    assert service.record_count() == 9306
    assert service.athlete_count() > 0


def test_expected_dataset_columns_are_available(
    service: AthleteDataService,
) -> None:
    df = service.dataframe

    expected = {
        "resolved_athlete_id",
        "year",
        "division",
        "equipment",
        "weight_class",
        "bodyweight",
        "best_squat",
        "best_bench",
        "best_deadlift",
        "total",
    }

    assert expected.issubset(df.columns)


def test_list_athletes(service: AthleteDataService) -> None:
    athletes = service.list_athletes()

    assert len(athletes) == service.athlete_count()
    assert len(athletes) > 0
    assert all(isinstance(athlete, str) for athlete in athletes)


def test_known_athlete_can_be_found(
    service: AthleteDataService,
) -> None:
    athlete_id = "ATH-3329e53259abce06"

    assert service.athlete_exists(athlete_id)

    athlete = service.find_athlete(athlete_id)

    assert athlete["resolved_athlete_id"] == "ATH-6ec70392619dedd1"
    assert athlete["athlete_id"] == athlete_id
    assert athlete["athlete_name"] == "PANNEERASELVAM S"
    assert athlete["competition_count"] >= 1
    assert athlete["latest_year"] >= athlete["first_year"]


def test_history_is_chronological(
    service: AthleteDataService,
) -> None:
    athlete_id = "ATH-3329e53259abce06"

    history = service.get_history(athlete_id)

    assert not history.empty
    assert history["year"].is_monotonic_increasing


def test_history_before_target_year(
    service: AthleteDataService,
) -> None:
    athlete_id = "ATH-3329e53259abce06"

    history = service.get_history(
        athlete_id,
        before_year=2020,
    )

    assert not history.empty
    assert (history["year"] < 2020).all()


def test_history_limit_returns_latest_records(
    service: AthleteDataService,
) -> None:
    athlete_id = "ATH-3329e53259abce06"

    full_history = service.get_history(athlete_id)
    limited_history = service.get_history(athlete_id, limit=1)

    assert len(limited_history) == 1
    assert limited_history.iloc[0]["year"] == full_history.iloc[-1]["year"]


def test_missing_athlete_is_handled(
    service: AthleteDataService,
) -> None:
    fake_id = "ATH-does-not-exist"

    assert not service.athlete_exists(fake_id)

    with pytest.raises(KeyError):
        service.find_athlete(fake_id)


def test_history_contains_prediction_fields(
    service: AthleteDataService,
) -> None:
    athlete_id = "ATH-3329e53259abce06"

    history = service.get_history(athlete_id)

    required = {
        "resolved_athlete_id",
        "year",
        "bodyweight",
        "squat_1",
        "squat_2",
        "squat_3",
        "best_squat",
        "bench_1",
        "bench_2",
        "bench_3",
        "best_bench",
        "deadlift_1",
        "deadlift_2",
        "deadlift_3",
        "best_deadlift",
        "total",
    }

    assert required.issubset(history.columns)


def test_history_does_not_mutate_service_dataframe(
    service: AthleteDataService,
) -> None:
    original = service.dataframe

    history = service.get_history(
        "ATH-3329e53259abce06",
        limit=1,
    )

    history["total"] = -999999

    current = service.dataframe

    pd.testing.assert_frame_equal(original, current)


def test_list_athlete_options_returns_ui_ready_records(
    service: AthleteDataService,
) -> None:
    options = service.list_athlete_options()

    assert options

    first = options[0]

    assert set(first) == {
        "resolved_athlete_id",
        "athlete_name",
        "division",
        "weight_class",
        "equipment",
        "latest_year",
    }

    assert first["resolved_athlete_id"].startswith("ATH-")
    assert first["athlete_name"]
    assert first["division"]
    assert first["weight_class"]
    assert first["equipment"]
    assert first["latest_year"].isdigit()