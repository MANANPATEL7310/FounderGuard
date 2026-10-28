"""Model registry: loads manifest, initializes adapters, handles health checks."""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from backend.adapters.model_a_adapter import ModelAAdapter
from backend.adapters.model_b_adapter import ModelBAdapter
from backend.adapters.model_c_adapter import ModelCAdapter
from backend.adapters.model_d_adapter import ModelDAdapter
from backend.config import MANIFEST_PATH, MODELS_DIR

logger = logging.getLogger(__name__)

class ModelRegistry:
    def __init__(self):
        self.manifest: Dict[str, Any] = {}
        self.adapters: Dict[str, Any] = {
            "model_a": ModelAAdapter(),
            "model_b": ModelBAdapter(),
            "model_c": ModelCAdapter(),
            "model_d": ModelDAdapter(),
        }
        self.load_status: Dict[str, str] = {k: "uninitialized" for k in self.adapters}
        self.is_ready: bool = False

    def load_all(self) -> None:
        """Loads manifest and initializes all 4 models."""
        if not MANIFEST_PATH.exists():
            raise FileNotFoundError(f"Model manifest not found at: {MANIFEST_PATH}")

        with open(MANIFEST_PATH, "r") as f:
            self.manifest = json.load(f)

        models_info = self.manifest.get("models", {})

        for model_id, adapter in self.adapters.items():
            try:
                info = models_info.get(model_id, {})
                folder_str = info.get("folder", f"models/{model_id}/v1")
                folder_path = Path(__file__).resolve().parent.parent / folder_str
                
                # Check for case variance (v1 vs V1)
                if not folder_path.exists():
                    v1_upper = folder_path.parent / "V1"
                    if v1_upper.exists():
                        folder_path = v1_upper

                adapter.load(folder_path)
                self.load_status[model_id] = "loaded"
                logger.info(f"Model {model_id} loaded successfully from {folder_path}")
            except Exception as e:
                self.load_status[model_id] = f"error: {str(e)}"
                logger.error(f"Failed to load {model_id}: {e}", exc_info=True)

        # Service is ready if all required models loaded
        self.is_ready = all(status == "loaded" for status in self.load_status.values())

    def get_adapter(self, model_id: str):
        return self.adapters.get(model_id)

    def get_models_info(self) -> Dict[str, Any]:
        """Returns metadata for the /v1/models endpoint."""
        return {
            "manifest_version": self.manifest.get("manifest_version", "1.0"),
            "environment": self.manifest.get("environment", {}),
            "load_status": self.load_status,
            "models": self.manifest.get("models", {})
        }

# Global registry singleton
registry = ModelRegistry()

