"""Model A Adapter: Startup Outcome Classifier."""
import time
import pickle
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import pandas as pd

from backend.adapters.base import BaseModelAdapter, load_module_from_file
from backend.config import MODEL_A_MAX_TRAINING_YEAR
from backend.schemas.envelope import ModelEnvelope

class ModelAAdapter(BaseModelAdapter):
    def __init__(self) -> None:
        super().__init__("model_a", "Startup Outcome Classifier")
        self.bundle: Any = None
        self.clf: Any = None
        self.sf: Any = None

    def load(self, artifact_dir: Path) -> None:
        p = Path(artifact_dir)
        # Load startup_features dynamically
        self.sf = load_module_from_file("startup_features", p / "startup_features.py")

        pkl_path = p / "startup_outcome_classifier.pkl"
        with open(pkl_path, "rb") as f:
            self.bundle = pickle.load(f)
        self.clf = self.bundle["model"]

    def check_applicability(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if not payload or not isinstance(payload, dict):
            return False, "Payload must be a dictionary."

        try:
            funding_raw = payload.get("funding_total_usd")
            funding = float(funding_raw) if funding_raw is not None else 0.0
            rounds_raw = payload.get("funding_rounds")
            rounds = int(rounds_raw) if rounds_raw is not None else 0
        except (ValueError, TypeError):
            return False, "Invalid funding_total_usd or funding_rounds value."

        if funding <= 0 or rounds <= 0:
            return False, "Model A is not applicable to pre-funding ideas (funding is 0 or rounds are 0)."

        founded = payload.get("founded_at")
        first = payload.get("first_funding_at")
        last = payload.get("last_funding_at")
        if not founded or not first or not last or str(founded).strip() == "" or str(first).strip() == "" or str(last).strip() == "":
            return False, "dates missing: founded_at, first_funding_at, and last_funding_at are required for Model A."

        # Verify dates are parseable
        for d_col in ["founded_at", "first_funding_at", "last_funding_at"]:
            val = str(payload.get(d_col) or "")
            dt = pd.to_datetime(val, errors="coerce")
            if pd.isna(dt):
                return False, f"dates missing or invalid: '{d_col}' could not be parsed as a date."

        return True, None

    def predict(self, payload: Dict[str, Any]) -> ModelEnvelope:
        start_t = time.perf_counter()
        if not payload or not isinstance(payload, dict):
            return ModelEnvelope(
                model_id=self.model_id,
                model_name=self.model_name,
                status="error",
                applicability_reason="Payload must be a dictionary",
                runtime_ms=0.0
            )

        is_app, reason = self.check_applicability(payload)
        if not is_app:
            return ModelEnvelope(
                model_id=self.model_id,
                model_name=self.model_name,
                status="not_applicable",
                applicability_reason=reason,
                data=None,
                warnings=[],
                runtime_ms=round((time.perf_counter() - start_t) * 1000, 2),
                inputs_used=["funding_total_usd", "funding_rounds", "founded_at", "first_funding_at", "last_funding_at"],
            )

        warnings = []
        try:
            # Check year drift against training data maximum
            years = []
            for d_col in ["founded_at", "first_funding_at", "last_funding_at"]:
                val = payload.get(d_col)
                if val:
                    dt = pd.to_datetime(str(val), errors="coerce")
                    if dt and not pd.isna(dt):
                        years.append(dt.year)

            if years and max(years) > MODEL_A_MAX_TRAINING_YEAR:
                warnings.append(
                    f"Founding or funding date year ({max(years)}) exceeds the training dataset's maximum year ({MODEL_A_MAX_TRAINING_YEAR}). "
                    f"Predictions on recent cohorts may experience temporal distribution drift."
                )

            # Ensure clean payload with exact RAW_COLS
            raw_cols = getattr(self.sf, "RAW_COLS", [
                'homepage_url', 'category_list', 'funding_total_usd', 'country_code', 'state_code',
                'region', 'city', 'funding_rounds', 'founded_at', 'first_funding_at', 'last_funding_at'
            ])
            clean_payload = {k: payload.get(k) for k in raw_cols}

            raw_df = pd.DataFrame([clean_payload])
            feats = self.sf.engineer_features(raw_df)

            # Native prediction
            probs = self.clf.predict_proba(feats)[0]
            pred = int(self.clf.predict(feats)[0])

            p_closed = round(float(probs[0]), 4)
            p_success = round(float(probs[1]), 4)
            outcome_label = "Operating / Acquired / IPO" if pred == 1 else "Closed"

            # Feature importances
            feat_names = list(self.clf.feature_names_)
            importances = self.clf.get_feature_importance()
            sorted_idx = importances.argsort()[::-1][:5]
            top_factors = [
                {
                    "feature": feat_names[i],
                    "value": str(feats[feat_names[i]].iloc[0]),
                    "importance": round(float(importances[i]), 2),
                }
                for i in sorted_idx
            ]

            data = {
                "model": "CatBoostClassifier",
                "target_definition": "Binary classification: 0 = Closed, 1 = Operating / Acquired / IPO",
                "predicted_outcome": outcome_label,
                "predicted_class": pred,
                "probabilities": {
                    "closed": p_closed,
                    "operating_acquired_ipo": p_success,
                },
                "confidence": max(p_closed, p_success),
                "top_contributing_features": top_factors,
                "warnings": warnings,
            }

            return ModelEnvelope(
                model_id=self.model_id,
                model_name=self.model_name,
                status="ok",
                data=data,
                warnings=warnings,
                runtime_ms=round((time.perf_counter() - start_t) * 1000, 2),
                inputs_used=list(payload.keys()),
            )
        except Exception as e:
            return ModelEnvelope(
                model_id=self.model_id,
                model_name=self.model_name,
                status="error",
                applicability_reason=str(e),
                data=None,
                warnings=[f"Execution failed: {str(e)}"],
                runtime_ms=round((time.perf_counter() - start_t) * 1000, 2),
                inputs_used=list(payload.keys()),
            )
