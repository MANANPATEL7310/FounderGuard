"""Model D Adapter: Multilabel Failure Category Classifier."""
import time
import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from backend.adapters.base import BaseModelAdapter, load_module_from_file
from backend.schemas.envelope import ModelEnvelope

class ModelDAdapter(BaseModelAdapter):
    def __init__(self):
        super().__init__("model_d", "Failure Category Classifier")
        self.clf = None
        self.md = None

    def load(self, artifact_dir: Path) -> None:
        p = Path(artifact_dir)
        # Load model_d_inference dynamically
        self.md = load_module_from_file("model_d_inference", p / "model_d_inference.py")

        self.clf = self.md.FailureCategoryClassifier(str(p))

    def check_applicability(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if not payload or not isinstance(payload, dict):
            return False, "Payload must be a dictionary."
        text = str(payload.get("text") or "").strip()
        if not text:
            return False, "Model D requires narrative text."
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
                inputs_used=["text"],
            )

        try:
            text = str(payload.get("text") or "").strip()
            top_k_raw = payload.get("top_k_cases")
            try:
                top_k = int(top_k_raw) if top_k_raw is not None else 3
            except (ValueError, TypeError):
                top_k = 3

            # Suppress spurious NumPy Accelerate BLAS matmul runtime warnings on macOS Apple Silicon
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                res = self.clf.predict(text, top_k_cases=top_k)
            warnings_list = res.get("warnings", [])

            return ModelEnvelope(
                model_id=self.model_id,
                model_name=self.model_name,
                status="ok",
                data=res,
                warnings=warnings_list,
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
