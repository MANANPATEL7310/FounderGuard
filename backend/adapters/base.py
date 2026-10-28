"""Base class for model adapters."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
from backend.schemas.envelope import ModelEnvelope

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
