"""Model D Adapter: Multilabel Failure Category Classifier."""
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from backend.adapters.base import BaseModelAdapter
from backend.schemas.envelope import ModelEnvelope

class ModelDAdapter(BaseModelAdapter):
    def __init__(self):
        super().__init__("model_d", "Failure Category Classifier")
        self.clf = None

    def load(self, artifact_dir: Path) -> None:
        p = Path(artifact_dir)
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
        import model_d_inference as md

        self.clf = md.FailureCategoryClassifier(str(p))

    def check_applicability(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        text = payload.get("text", "").strip()
        if not text:
            return False, "Model D requires narrative text."
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
                inputs_used=["text"],
            )

        try:
            text = payload.get("text", "")
            top_k = int(payload.get("top_k_cases", 3))

            res = self.clf.predict(text, top_k_cases=top_k)
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
