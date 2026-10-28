"""Model C Adapter: PyTorch BiGRU Idea Evaluator & Aspect Extractor."""
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from backend.adapters.base import BaseModelAdapter, load_module_from_file
from backend.schemas.envelope import ModelEnvelope

class ModelCAdapter(BaseModelAdapter):
    bundle: Any = None
    mc: Any = None

    def __init__(self) -> None:
        super().__init__("model_c", "PyTorch BiGRU Idea Evaluator")
        self.bundle = None
        self.mc = None

    def load(self, artifact_dir: Path) -> None:
        p = Path(artifact_dir)
        # Load model_c_inference dynamically
        self.mc = load_module_from_file("model_c_inference", p / "model_c_inference.py")

        encoder_pt = p / "model_c_encoder.pt"
        self.bundle = self.mc.load_bundle(str(encoder_pt))

    def check_applicability(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if not payload or not isinstance(payload, dict):
            return False, "Payload must be a dictionary."
        text = str(payload.get("idea_text") or "").strip()
        if not text:
            return False, "Model C requires an idea pitch / description."
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
                inputs_used=["idea_text"],
            )

        try:
            if self.mc is None or self.bundle is None:
                raise RuntimeError("Model C adapter is not loaded. Call load() before predict().")

            idea_text = str(payload.get("idea_text") or "").strip()
            declared_sector = payload.get("declared_sector")
            if declared_sector is not None:
                declared_sector = str(declared_sector).strip() or None

            extra_raw = payload.get("extra")
            extra = dict(extra_raw) if isinstance(extra_raw, dict) else {}

            res = self.mc.evaluate_idea(
                self.bundle,
                idea_text,
                declared_sector=declared_sector,
                extra=extra
            )
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
