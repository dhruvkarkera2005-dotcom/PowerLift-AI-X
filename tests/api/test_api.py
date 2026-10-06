from __future__ import annotations

from fastapi.testclient import TestClient

from powerlift_ai_x.api.main import app


client = TestClient(app)


ATHLETE_ID = "ATH-bf636574800eaf3e"


def _history() -> list[dict]:
    return [
        {
            "resolved_athlete_id": ATHLETE_ID,
            "year": 2018,
            "total": 525.0,
            "best_squat": 185.0,
            "best_bench": 110.0,
            "best_deadlift": 230.0,
            "bodyweight": 74.0,
        },
        {
            "resolved_athlete_id": ATHLETE_ID,
            "year": 2019,
            "total": 647.5,
            "best_squat": 245.0,
            "best_bench": 145.0,
            "best_deadlift": 257.5,
            "bodyweight": 82.20,
        },
        {
            "resolved_athlete_id": ATHLETE_ID,
            "year": 2022,
            "total": 755.0,
            "best_squat": 290.0,
            "best_bench": 185.0,
            "best_deadlift": 280.0,
            "bodyweight": 82.06,
        },
    ]


def _valid_payload() -> dict:
    return {
        "athlete_id": ATHLETE_ID,
        "target_year": 2024,
        "division": "Open",
        "weight_class": "93",
        "equipment": "EQUIPPED",
        "history": _history(),
    }


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["project"] == "PowerLift-AI-X"
    assert data["models_loaded"] is True
    assert data["preprocessor_loaded"] is True


def test_predict_success():
    response = client.post(
        "/predict",
        json=_valid_payload(),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["athlete_id"] == ATHLETE_ID
    assert data["target_year"] == 2024

    predictions = data["predictions"]

    assert set(predictions) == {
        "future_best_squat",
        "future_best_bench",
        "future_best_deadlift",
        "future_total",
    }

    for value in predictions.values():
        assert isinstance(value, float)
        assert value == value
        assert value != float("inf")
        assert value != float("-inf")


def test_predict_rejects_future_history():
    payload = _valid_payload()

    payload["history"][0]["year"] = 2024

    response = client.post(
        "/predict",
        json=payload,
    )

    assert response.status_code == 400


def test_predict_requires_history():
    payload = _valid_payload()

    payload["history"] = []

    response = client.post(
        "/predict",
        json=payload,
    )

    assert response.status_code == 422


def test_predict_requires_target_year():
    payload = _valid_payload()

    del payload["target_year"]

    response = client.post(
        "/predict",
        json=payload,
    )

    assert response.status_code == 422