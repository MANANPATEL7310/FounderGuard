"""Orchestrator: runs model adapters in parallel with timeouts and error isolation."""
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Tuple

from backend.config import MODEL_TIMEOUT_SECONDS
from backend.registry import registry
from backend.schemas.envelope import ModelEnvelope

logger = logging.getLogger(__name__)

class Orchestrator:
    @staticmethod
    def run_all_models(normalized: Dict[str, Any]) -> Dict[str, ModelEnvelope]:
        """
        Executes all 4 models in parallel with per-model isolation and timeout.
        Returns a dictionary mapping model_id -> ModelEnvelope.
        """
        payloads = {
            "model_a": normalized.get("model_a_payload", {}),
            "model_b": normalized.get("model_b_payload", {}),
            "model_c": normalized.get("model_c_payload", {}),
            "model_d": normalized.get("model_d_payload", {}),
        }

        results: Dict[str, ModelEnvelope] = {}

        def _run_single(model_id: str, payload: Dict[str, Any]) -> Tuple[str, ModelEnvelope]:
            adapter = registry.get_adapter(model_id)
            if not adapter:
                return model_id, ModelEnvelope(
                    model_id=model_id,
                    model_name=model_id,
                    status="error",
                    applicability_reason="Adapter not registered",
                    runtime_ms=0.0
                )
            try:
                env = adapter.predict(payload)
                return model_id, env
            except Exception as e:
                logger.error(f"Unhandled error in adapter {model_id}: {e}", exc_info=True)
                return model_id, ModelEnvelope(
                    model_id=model_id,
                    model_name=adapter.model_name,
                    status="error",
                    applicability_reason=str(e),
                    warnings=[f"Adapter crashed: {str(e)}"],
                    runtime_ms=0.0
                )

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_model = {
                executor.submit(_run_single, m_id, payloads[m_id]): m_id
                for m_id in payloads
            }

            for future in as_completed(future_to_model):
                m_id = future_to_model[future]
                try:
                    res_id, env = future.result(timeout=MODEL_TIMEOUT_SECONDS)
                    results[res_id] = env
                except Exception as e:
                    logger.warning(f"Model {m_id} timed out or failed in executor: {e}")
                    results[m_id] = ModelEnvelope(
                        model_id=m_id,
                        model_name=m_id,
                        status="error",
                        applicability_reason=f"Timeout or executor error: {str(e)}",
                        warnings=["Model execution timed out"],
                        runtime_ms=float(MODEL_TIMEOUT_SECONDS * 1000)
                    )

        return results
