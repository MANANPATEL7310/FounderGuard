"""Base class and dynamic loader for model adapters."""
import importlib.util
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from backend.schemas.envelope import ModelEnvelope

def load_module_from_file(module_name: str, file_path: Path) -> Any:
    """
    Dynamically loads a python module from file path and registers it in sys.modules.
    Avoids static linter/IDE unresolved import errors.
    """
    p = Path(file_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Module file not found: {p}")

    parent_str = str(p.parent)
    if parent_str not in sys.path:
        sys.path.insert(0, parent_str)

    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, str(p))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module spec for '{module_name}' from {p}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

class BaseModelAdapter(ABC):
    def __init__(self, model_id: str, model_name: str):
        self.model_id = model_id
        self.model_name = model_name

    @abstractmethod
    def load(self, artifact_dir: Any) -> None:
        """Load artifacts into memory."""
        pass

    @abstractmethod
    def check_applicability(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Check whether this model applies to the given payload.
        Returns (is_applicable, reason_if_not).
        """
        pass

    @abstractmethod
    def predict(self, payload: Dict[str, Any]) -> ModelEnvelope:
        """
        Execute prediction and return standardized envelope.
        Must never raise uncaught exceptions; errors should be caught and returned in envelope.
        """
        pass
