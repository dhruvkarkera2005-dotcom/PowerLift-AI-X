from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd


# ============================================================
# POWERLIFT-AI-X MODEL SERVICE
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

ARTIFACT_DIR = (
    PROJECT_ROOT
    / "notebooks"
    / "artifacts"
    / "powerlift_ai_x_models"
)


PREPROCESSOR_PATH = (
    ARTIFACT_DIR
    / "preprocessor.joblib"
)


MODEL_PATHS = {
    "future_best_squat":
        ARTIFACT_DIR
        / "best_squat_model.joblib",

    "future_best_bench":
        ARTIFACT_DIR
        / "best_bench_model.joblib",

    "future_best_deadlift":
        ARTIFACT_DIR
        / "best_deadlift_model.joblib",

    "future_total":
        ARTIFACT_DIR
        / "total_model.joblib",
}


# ============================================================
# PRODUCTION FEATURE CONTRACT
# ============================================================

PRODUCTION_FEATURES = [
    "year",
    "division",
    "weight_class",
    "equipment",
    "previous_year_count",
    "previous_year",
    "years_since_previous",
    "previous_total",
    "previous_squat",
    "previous_bench",
    "previous_deadlift",
    "previous_bodyweight",
    "historical_mean_total",
    "historical_max_total",
    "historical_min_total",
    "historical_std_total",
    "historical_max_squat",
    "historical_max_bench",
    "historical_max_deadlift",
    "historical_mean_bodyweight",
    "previous_total_change",
    "previous_total_change_pct",
]


TARGETS = [
    "future_best_squat",
    "future_best_bench",
    "future_best_deadlift",
    "future_total",
]


class PowerLiftModelService:
    """
    Production inference service for PowerLift-AI-X.

    Loads the fitted preprocessing pipeline and the four
    locked target-specific regression models.
    """

    def __init__(
        self,
        artifact_dir: Path = ARTIFACT_DIR,
    ) -> None:

        self.artifact_dir = Path(
            artifact_dir
        )

        self.preprocessor = None

        self.models: dict[str, Any] = {}

        self._load_artifacts()


    # ========================================================
    # LOAD ARTIFACTS
    # ========================================================

    def _load_artifacts(self) -> None:

        preprocessor_path = (
            self.artifact_dir
            / "preprocessor.joblib"
        )

        if not preprocessor_path.exists():

            raise FileNotFoundError(
                "Preprocessor artifact not found: "
                f"{preprocessor_path}"
            )


        self.preprocessor = joblib.load(
            preprocessor_path
        )


        model_filenames = {
            "future_best_squat":
                "best_squat_model.joblib",

            "future_best_bench":
                "best_bench_model.joblib",

            "future_best_deadlift":
                "best_deadlift_model.joblib",

            "future_total":
                "total_model.joblib",
        }


        for target, filename in (
            model_filenames.items()
        ):

            model_path = (
                self.artifact_dir
                / filename
            )


            if not model_path.exists():

                raise FileNotFoundError(
                    f"Model artifact not found: "
                    f"{model_path}"
                )


            self.models[target] = (
                joblib.load(model_path)
            )


    # ========================================================
    # FEATURE VALIDATION
    # ========================================================

    def validate_features(
        self,
        input_data: pd.DataFrame,
    ) -> None:

        if not isinstance(
            input_data,
            pd.DataFrame,
        ):

            raise TypeError(
                "input_data must be a "
                "pandas DataFrame."
            )


        missing_features = [
            feature
            for feature in PRODUCTION_FEATURES
            if feature not in input_data.columns
        ]


        if missing_features:

            raise ValueError(
                "Missing required ML features: "
                + ", ".join(
                    missing_features
                )
            )


    # ========================================================
    # PREDICT
    # ========================================================

    def predict(
        self,
        input_data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Generate predictions for one or more rows.

        input_data must already contain the exact 22
        production ML features.
        """

        self.validate_features(
            input_data
        )


        X = input_data[
            PRODUCTION_FEATURES
        ].copy()


        X_processed = (
            self.preprocessor.transform(X)
        )


        predictions = pd.DataFrame(
            index=input_data.index
        )


        for target in TARGETS:

            predictions[target] = (
                self.models[target]
                .predict(X_processed)
            )


        return predictions


    # ========================================================
    # HEALTH CHECK
    # ========================================================

    def health(self) -> Mapping[str, Any]:

        return {
            "status": "ok",
            "project": "PowerLift-AI-X",
            "models_loaded": len(
                self.models
            ) == 4,
            "preprocessor_loaded":
                self.preprocessor is not None,
            "targets_loaded": list(
                self.models.keys()
            ),
        }