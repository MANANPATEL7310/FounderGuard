"""Model B Adapter: Failure Risk Estimator."""
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import joblib

from backend.adapters.base import BaseModelAdapter, load_module_from_file
from backend.schemas.envelope import ModelEnvelope

class ModelBAdapter(BaseModelAdapter):
    bundle: Any = None
    mb: Any = None

    def __init__(self) -> None:
        super().__init__("model_b", "LogisticRegression + Platt calibration")
        self.bundle = None
        self.mb = None

    def load(self, artifact_dir: Path) -> None:
        p = Path(artifact_dir)
        # Load model_b_inference dynamically
        self.mb = load_module_from_file("model_b_inference", p / "model_b_inference.py")

        joblib_path = p / "model_b_failure_risk.joblib"
        self.bundle = joblib.load(joblib_path)

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

        if funding <= 0 or rounds < 1:
            return False, "Model B was trained on funded startups: funding_total_usd > 0 and funding_rounds >= 1 required."

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
                inputs_used=["funding_total_usd", "funding_rounds"],
            )

        try:
            if self.mb is None or self.bundle is None:
                raise RuntimeError("Model B adapter is not loaded. Call load() before predict().")

            clean_payload = {
                "category_code": str(payload.get("category_code") or "other").lower(),
                "state_code": str(payload.get("state_code") or "OTHER").upper(),
                "funding_total_usd": float(payload.get("funding_total_usd") or 0.0),
                "funding_rounds": int(payload.get("funding_rounds") or 1),
                "has_VC": int(bool(payload.get("has_VC", 0))),
                "has_angel": int(bool(payload.get("has_angel", 0))),
                "has_roundA": int(bool(payload.get("has_roundA", 0))),
                "has_roundB": int(bool(payload.get("has_roundB", 0))),
                "has_roundC": int(bool(payload.get("has_roundC", 0))),
                "has_roundD": int(bool(payload.get("has_roundD", 0))),
            }

            res = self.mb.predict_failure_risk(self.bundle, clean_payload)
            warnings = res.get("warnings", [])

            return ModelEnvelope(
                model_id=self.model_id,
                model_name=self.model_name,
                status="ok",
                data=res,
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
