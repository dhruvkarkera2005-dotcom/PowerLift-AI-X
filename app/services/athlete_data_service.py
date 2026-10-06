from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


class AthleteDataService:
    """
    Application data-access layer for PowerLift-AI-X athlete history.

    Data sources:
    - Canonical resolved JSONL:
        Authoritative source for athlete identity, name, and resolved ID.
    - ML Excel:
        Prediction-eligible competition records.

    The ML dataset is NOT modified on disk.

    A validated record-level bridge is built between the two datasets using:

        athlete_id
        year
        competition
        date_of_birth

    This avoids relying on the stale resolved_athlete_id values that were
    present in the older ML dataset.
    """

    REQUIRED_COLUMNS = {
        "athlete_id",
        "resolved_athlete_id",
        "year",
        "competition",
        "division",
        "equipment",
        "weight_class",
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
        "place",
        "lot",
        "team",
        "date_of_birth",
        "identity_confidence",
    }

    CANONICAL_COLUMNS = {
        "athlete_id",
        "resolved_athlete_id",
        "athlete_name",
        "year",
        "competition",
        "date_of_birth",
    }

    NUMERIC_COLUMNS = [
        "year",
        "weight_class",
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
        "place",
        "lot",
    ]

    HISTORY_COLUMNS = [
        "resolved_athlete_id",
        "athlete_name",
        "year",
        "competition",
        "division",
        "equipment",
        "weight_class",
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
        "place",
        "lot",
        "team",
        "date_of_birth",
        "identity_confidence",
        "athlete_id",
    ]

    BRIDGE_KEYS = [
        "athlete_id",
        "year",
        "competition",
        "date_of_birth",
    ]

    def __init__(
        self,
        dataset_path: str | Path | None = None,
        canonical_path: str | Path | None = None,
    ) -> None:
        project_root = Path(__file__).resolve().parents[2]

        if dataset_path is None:
            dataset_path = (
                project_root
                / "data"
                / "final"
                / "ml"
                / "powerlift_ai_x_ml_dataset.xlsx"
            )

        if canonical_path is None:
            canonical_path = (
                project_root
                / "data"
                / "final"
                / "competition_results_resolved.jsonl"
            )

        self.dataset_path = Path(dataset_path)
        self.canonical_path = Path(canonical_path)

        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"PowerLift-AI-X ML dataset not found: {self.dataset_path}"
            )

        if not self.canonical_path.exists():
            raise FileNotFoundError(
                "PowerLift-AI-X resolved canonical dataset not found: "
                f"{self.canonical_path}"
            )

        self._df = self._load_and_bridge()

    def _load_and_bridge(self) -> pd.DataFrame:
        """Load the ML dataset and attach canonical identity information."""

        ml_df = self._load_ml_dataset()
        canonical_df = self._load_canonical_dataset()

        bridge = self._build_identity_bridge(
            ml_df,
            canonical_df,
        )

        # Remove the stale resolved ID from the ML dataset.
        ml_df = ml_df.drop(
            columns=["resolved_athlete_id"]
        )

        # Attach the authoritative canonical identity and name.
        ml_df = ml_df.merge(
            bridge[
                [
                    *self.BRIDGE_KEYS,
                    "resolved_athlete_id",
                    "athlete_name",
                    "canonical_identity_confidence",
                ]
            ],
            on=self.BRIDGE_KEYS,
            how="left",
            validate="many_to_one",
        )

        if ml_df["resolved_athlete_id"].isna().any():
            count = int(
                ml_df["resolved_athlete_id"].isna().sum()
            )

            raise ValueError(
                "Identity bridge produced missing resolved "
                f"athlete IDs for {count} ML records."
            )

        # Canonical identity confidence is authoritative.
        ml_df["identity_confidence"] = (
            ml_df["canonical_identity_confidence"]
            .astype("string")
        )

        ml_df = ml_df.drop(
            columns=["canonical_identity_confidence"]
        )

        # Keep deterministic ordering.
        ml_df = ml_df.sort_values(
            by=[
                "resolved_athlete_id",
                "year",
                "competition",
            ],
            kind="stable",
            na_position="last",
        ).reset_index(drop=True)

        return ml_df

    def _load_ml_dataset(self) -> pd.DataFrame:
        """Load and validate the prediction-eligible ML dataset."""

        df = pd.read_excel(
            self.dataset_path
        )

        missing_columns = (
            self.REQUIRED_COLUMNS.difference(df.columns)
        )

        if missing_columns:
            missing = ", ".join(
                sorted(missing_columns)
            )

            raise ValueError(
                "ML dataset is missing required columns: "
                f"{missing}"
            )

        df = df.copy()

        self._normalize_string_columns(
            df,
            [
                "athlete_id",
                "resolved_athlete_id",
                "competition",
                "division",
                "equipment",
                "team",
                "date_of_birth",
                "identity_confidence",
            ],
        )

        self._normalize_numeric_columns(
            df
        )

        return df

    def _load_canonical_dataset(self) -> pd.DataFrame:
        """Load the resolved canonical JSONL identity dataset."""

        records: list[dict[str, Any]] = []

        with self.canonical_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for line_number, line in enumerate(
                handle,
                start=1,
            ):
                line = line.strip()

                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        "Invalid JSON in resolved canonical dataset "
                        f"at line {line_number}: {exc}"
                    ) from exc

                records.append(record)

        if not records:
            raise ValueError(
                "Resolved canonical dataset is empty: "
                f"{self.canonical_path}"
            )

        df = pd.DataFrame(records)

        missing_columns = (
            self.CANONICAL_COLUMNS.difference(df.columns)
        )

        if missing_columns:
            missing = ", ".join(
                sorted(missing_columns)
            )

            raise ValueError(
                "Resolved canonical dataset is missing required "
                f"columns: {missing}"
            )

        df = df.copy()

        self._normalize_string_columns(
            df,
            [
                "athlete_id",
                "resolved_athlete_id",
                "athlete_name",
                "competition",
                "date_of_birth",
            ],
        )

        df["year"] = pd.to_numeric(
            df["year"],
            errors="coerce",
        ).astype("Int64")

        return df

    def _build_identity_bridge(
        self,
        ml_df: pd.DataFrame,
        canonical_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Build and validate the ML → canonical identity bridge.

        Each ML record key must resolve to exactly one canonical
        resolved athlete ID.
        """

        bridge = canonical_df[
            [
                *self.BRIDGE_KEYS,
                "resolved_athlete_id",
                "athlete_name",
                "identity_confidence",
            ]
        ].copy()

        bridge = bridge.rename(
            columns={
                "identity_confidence":
                    "canonical_identity_confidence",
            }
        )

        # A single bridge key must never point to multiple
        # resolved athlete IDs.
        key_counts = (
            bridge
            .groupby(
                self.BRIDGE_KEYS,
                dropna=False,
            )["resolved_athlete_id"]
            .nunique()
        )

        ambiguous = key_counts[
            key_counts > 1
        ]

        if not ambiguous.empty:
            examples = ambiguous.head(
                10
            ).to_dict()

            raise ValueError(
                "Canonical identity bridge is ambiguous. "
                f"{len(ambiguous)} bridge keys map to multiple "
                "resolved athlete IDs. "
                f"Examples: {examples}"
            )

        bridge = bridge.drop_duplicates(
            subset=self.BRIDGE_KEYS,
            keep="first",
        )

        # Check every ML record key exists in canonical data.
        ml_keys = ml_df[
            self.BRIDGE_KEYS
        ].drop_duplicates()

        matched = ml_keys.merge(
            bridge[self.BRIDGE_KEYS],
            on=self.BRIDGE_KEYS,
            how="left",
            indicator=True,
        )

        unmatched = matched[
            matched["_merge"] == "left_only"
        ]

        if not unmatched.empty:
            examples = unmatched.head(
                10
            ).to_dict("records")

            raise ValueError(
                "Identity bridge could not match all ML records. "
                f"{len(unmatched)} ML record keys are unmatched. "
                f"Examples: {examples}"
            )

        resolved = ml_keys.merge(
            bridge,
            on=self.BRIDGE_KEYS,
            how="left",
            validate="one_to_one",
        )

        if resolved[
            "resolved_athlete_id"
        ].isna().any():
            count = int(
                resolved[
                    "resolved_athlete_id"
                ].isna().sum()
            )

            raise ValueError(
                "Identity bridge validation failed: "
                f"{count} ML keys have no resolved athlete ID."
            )

        if resolved[
            "athlete_name"
        ].isna().any():
            count = int(
                resolved[
                    "athlete_name"
                ].isna().sum()
            )

            raise ValueError(
                "Identity bridge validation failed: "
                f"{count} ML keys have no athlete name."
            )

        return resolved

    @staticmethod
    def _normalize_string_columns(
        df: pd.DataFrame,
        columns: list[str],
    ) -> None:
        """Normalize string columns in-place."""

        for column in columns:
            if column in df.columns:
                df[column] = (
                    df[column]
                    .astype("string")
                    .str.strip()
                )

    def _normalize_numeric_columns(
        self,
        df: pd.DataFrame,
    ) -> None:
        """Normalize numeric columns in-place."""

        for column in self.NUMERIC_COLUMNS:
            if column in df.columns:
                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce",
                )

        df["year"] = df[
            "year"
        ].astype("Int64")

        df["weight_class"] = df[
            "weight_class"
        ].astype("Int64")

    @property
    def dataframe(self) -> pd.DataFrame:
        """Return a defensive copy of the complete application dataset."""

        return self._df.copy()

    def athlete_count(self) -> int:
        """Return the number of unique resolved athletes."""

        return int(
            self._df[
                "resolved_athlete_id"
            ]
            .dropna()
            .nunique()
        )

    def record_count(self) -> int:
        """Return the number of competition records."""

        return int(
            len(self._df)
        )

    def list_athletes(self) -> list[str]:
        """
        Return all current canonical resolved athlete IDs.
        """

        return (
            self._df[
                "resolved_athlete_id"
            ]
            .dropna()
            .astype(str)
            .drop_duplicates()
            .sort_values()
            .tolist()
        )

    def list_athlete_options(self) -> list[dict[str, str]]:
        """Return prediction-eligible athletes in a UI-friendly format."""

        options = (
            self._df[
                [
                    "resolved_athlete_id",
                    "athlete_name",
                    "division",
                    "weight_class",
                    "equipment",
                    "year",
                ]
            ]
            .dropna(
                subset=[
                    "resolved_athlete_id",
                    "athlete_name",
                ]
            )
            .sort_values(
                ["athlete_name", "year"],
                ascending=[True, False],
            )
            .drop_duplicates(
                subset=["resolved_athlete_id"],
                keep="first",
            )
            .reset_index(drop=True)
        )

        return [
            {
                "resolved_athlete_id": str(
                    row["resolved_athlete_id"]
                ),
                "athlete_name": str(
                    row["athlete_name"]
                ),
                "division": str(
                    row["division"]
                ),
                "weight_class": str(
                    row["weight_class"]
                ),
                "equipment": str(
                    row["equipment"]
                ),
                "latest_year": str(
                    row["year"]
                ),
            }
            for _, row in options.iterrows()
        ]

    def resolve_athlete_id(
        self,
        athlete_id: str,
    ) -> str:
        """
        Resolve either a current canonical resolved ID or an
        original athlete ID to the current canonical resolved ID.

        The original ID is supported as a backward-compatible
        lookup alias.

        Raises:
            KeyError: if the athlete cannot be resolved.
        """

        athlete_id = str(
            athlete_id
        ).strip()

        if not athlete_id:
            raise KeyError(
                "Athlete ID cannot be empty"
            )

        # Current canonical resolved ID.
        if bool(
            (
                self._df[
                    "resolved_athlete_id"
                ]
                == athlete_id
            ).any()
        ):
            return athlete_id

        # Backward-compatible original athlete ID.
        matches = (
            self._df[
                self._df[
                    "athlete_id"
                ] == athlete_id
            ][
                "resolved_athlete_id"
            ]
            .dropna()
            .drop_duplicates()
        )

        if len(matches) == 1:
            return str(
                matches.iloc[0]
            )

        if len(matches) > 1:
            raise KeyError(
                "Original athlete ID maps to multiple "
                f"canonical athletes: {athlete_id}"
            )

        raise KeyError(
            f"Athlete not found: {athlete_id}"
        )

    def athlete_exists(
        self,
        athlete_id: str,
    ) -> bool:
        """Return True when the athlete can be resolved."""

        try:
            self.resolve_athlete_id(
                athlete_id
            )
            return True
        except KeyError:
            return False

    def find_athlete(
        self,
        athlete_id: str,
    ) -> dict[str, Any]:
        """
        Return basic information about an athlete.

        Raises:
            KeyError: if the athlete does not exist.
        """

        athlete_id = self.resolve_athlete_id(
            athlete_id
        )

        history = self.get_history(
            athlete_id
        )

        if history.empty:
            raise KeyError(
                f"Athlete not found: {athlete_id}"
            )

        latest = history.iloc[-1]

        return {
            "resolved_athlete_id": athlete_id,
            "athlete_name": self._clean_value(
                latest["athlete_name"]
            ),
            "athlete_id": self._clean_value(
                latest["athlete_id"]
            ),
            "division": self._clean_value(
                latest["division"]
            ),
            "equipment": self._clean_value(
                latest["equipment"]
            ),
            "weight_class": self._clean_value(
                latest["weight_class"]
            ),
            "date_of_birth": self._clean_value(
                latest["date_of_birth"]
            ),
            "team": self._clean_value(
                latest["team"]
            ),
            "identity_confidence": self._clean_value(
                latest["identity_confidence"]
            ),
            "competition_count": int(
                len(history)
            ),
            "first_year": self._clean_value(
                history["year"].min()
            ),
            "latest_year": self._clean_value(
                history["year"].max()
            ),
        }

    def get_history(
        self,
        athlete_id: str,
        *,
        before_year: int | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """
        Return an athlete's competition history.

        Args:
            athlete_id:
                Current canonical resolved ID or a
                backward-compatible original athlete ID.

            before_year:
                If supplied, only records with year < before_year
                are returned.

            limit:
                If supplied, return only the most recent N records.
        """

        athlete_id = self.resolve_athlete_id(
            athlete_id
        )

        history = self._df[
            self._df[
                "resolved_athlete_id"
            ] == athlete_id
        ].copy()

        if before_year is not None:
            history = history[
                history["year"]
                < int(before_year)
            ].copy()

        history = history.sort_values(
            by=[
                "year",
                "competition",
            ],
            kind="stable",
            na_position="last",
        )

        if limit is not None:
            if limit <= 0:
                raise ValueError(
                    "limit must be greater than zero"
                )

            history = history.tail(
                limit
            )

        return history[
            self.HISTORY_COLUMNS
        ].reset_index(
            drop=True
        )

    def get_latest_record(
        self,
        athlete_id: str,
    ) -> dict[str, Any]:
        """Return the athlete's most recent competition record."""

        history = self.get_history(
            athlete_id
        )

        if history.empty:
            raise KeyError(
                f"Athlete not found: {athlete_id}"
            )

        return self._row_to_dict(
            history.iloc[-1]
        )

    def get_competition_results(
        self,
        *,
        division: str | None = None,
        weight_class: int | str | None = None,
        equipment: str | None = None,
        competition: str | None = None,
        year: int | None = None,
        before_year: int | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """
        Return real competition results matching the supplied filters.

        This method is intended for category-level analysis such as:
        podium thresholds, competitor analysis, competition outlook,
        and historical category comparisons.

        The returned data comes from the application dataset already
        loaded and identity-resolved by this service.
        """

        results = self._df.copy()

        # ----------------------------------------------------
        # Optional filters
        # ----------------------------------------------------

        if division is not None:
            division_value = str(
                division
            ).strip()

            results = results[
                results["division"]
                .astype(str)
                .str.strip()
                == division_value
            ].copy()

        if weight_class is not None:
            try:
                weight_class_value = int(
                    weight_class
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ValueError(
                    "weight_class must be an integer-compatible value."
                ) from exc

            results = results[
                results["weight_class"]
                == weight_class_value
            ].copy()

        if equipment is not None:
            equipment_value = (
                str(equipment)
                .strip()
                .upper()
            )

            results = results[
                results["equipment"]
                .astype(str)
                .str.strip()
                .str.upper()
                == equipment_value
            ].copy()

        if competition is not None:
            competition_value = (
                str(competition)
                .strip()
            )

            results = results[
                results["competition"]
                .astype(str)
                .str.strip()
                == competition_value
            ].copy()

        if year is not None:
            results = results[
                results["year"]
                == int(year)
            ].copy()

        if before_year is not None:
            results = results[
                results["year"]
                < int(before_year)
            ].copy()

        # ----------------------------------------------------
        # Deterministic ordering
        # ----------------------------------------------------

        results = results.sort_values(
            by=[
                "year",
                "competition",
                "place",
                "total",
                "athlete_name",
            ],
            ascending=[
                False,
                True,
                True,
                False,
                True,
            ],
            kind="stable",
            na_position="last",
        )

        # ----------------------------------------------------
        # Optional limit
        # ----------------------------------------------------

        if limit is not None:
            if limit <= 0:
                raise ValueError(
                    "limit must be greater than zero."
                )

            results = results.head(
                limit
            )

        return results.reset_index(
            drop=True
        )

    @staticmethod
    def _clean_value(
        value: Any,
    ) -> Any:
        """Convert pandas missing values into Python None."""

        if pd.isna(value):
            return None

        if isinstance(
            value,
            pd.Timestamp,
        ):
            return value.isoformat()

        if hasattr(
            value,
            "item",
        ):
            try:
                return value.item()
            except (
                ValueError,
                TypeError,
            ):
                pass

        return value

    @classmethod
    def _row_to_dict(
        cls,
        row: pd.Series,
    ) -> dict[str, Any]:
        """Convert a dataframe row into JSON-safe Python values."""

        return {
            column: cls._clean_value(
                row[column]
            )
            for column in row.index
        }