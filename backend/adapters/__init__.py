"""Model adapters package."""
from backend.adapters.base import BaseModelAdapter
from backend.adapters.model_a_adapter import ModelAAdapter
from backend.adapters.model_b_adapter import ModelBAdapter
from backend.adapters.model_c_adapter import ModelCAdapter
from backend.adapters.model_d_adapter import ModelDAdapter

__all__ = [
    "BaseModelAdapter",
    "ModelAAdapter",
    "ModelBAdapter",
    "ModelCAdapter",
    "ModelDAdapter",
]

