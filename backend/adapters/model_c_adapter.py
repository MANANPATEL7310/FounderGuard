"""Model C Adapter: PyTorch BiGRU Idea Evaluator & Aspect Extractor."""
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from backend.adapters.base import BaseModelAdapter
from backend.schemas.envelope import ModelEnvelope

class ModelCAdapter(BaseModelAdapter):
    def __init__(self):
        super().__init__("model_c", "PyTorch BiGRU Idea Evaluator")
        self.bundle = None
        self.mc = None

    def load(self, artifact_dir: Path) -> None:
        p = Path(artifact_dir)
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
        import model_c_inference as mc
        self.mc = mc

        encoder_pt = p / "model_c_encoder.pt"
        self.bundle = mc.load_bundle(str(encoder_pt))

    def check_applicability(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        text = payload.get("idea_text", "").strip()
        if not text:
            return False, "Model C requires an idea pitch / description."
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
                inputs_used=["idea_text"],
            )

        try:
            idea_text = payload.get("idea_text", "")
            declared_sector = payload.get("declared_sector")
            extra = payload.get("extra", {})

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
