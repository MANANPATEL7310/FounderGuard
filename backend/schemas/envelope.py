"""Standard model result envelope schema."""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

class ModelEnvelope(BaseModel):
    model_id: str = Field(description="Identifier of the model: model_a, model_b, model_c, model_d")
    model_name: str = Field(description="Display name of the model")
    status: Literal["ok", "not_applicable", "error"] = Field(description="Execution status")
    applicability_reason: Optional[str] = Field(default=None, description="Plain language reason when not applicable")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Native structured model outputs")
    warnings: List[str] = Field(default_factory=list, description="Warnings from model and backend normalization")
    runtime_ms: float = Field(default=0.0, description="Execution time in milliseconds")
    inputs_used: List[str] = Field(default_factory=list, description="Names of inputs used by the model")

