"""Model B Adapter: Failure Risk Estimator."""
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import joblib

from backend.adapters.base import BaseModelAdapter
from backend.schemas.envelope import ModelEnvelope

class ModelBAdapter(BaseModelAdapter):
    def __init__(self):
        super().__init__("model_b", "LogisticRegression + Platt calibration")
        self.bundle = None
        self.mb = None

    def load(self, artifact_dir: Path) -> None:
        p = Path(artifact_dir)
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
        import model_b_inference as mb
        self.mb = mb

        joblib_path = p / "model_b_failure_risk.joblib"
        self.bundle = joblib.load(joblib_path)

    def check_applicability(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        funding = float(payload.get("funding_total_usd") or 0.0)
        rounds = int(payload.get("funding_rounds") or 0)
        if funding <= 0 or rounds < 1:
            return False, "Model B was trained on funded startups: funding_total_usd > 0 and funding_rounds >= 1 required."
        return True, None

    def predict(self, payload: Dict[str, Any]) -> ModelEnvelope:
        start_t = time.perf_counter()
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
            # Model B inference module validates and runs
            res = self.mb.predict_failure_risk(self.bundle, payload)
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
