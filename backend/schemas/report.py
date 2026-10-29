"""Schema for the full 8-section Evaluation Report."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.schemas.envelope import ModelEnvelope

class EvaluationMeta(BaseModel):
    evaluation_id: str
    parent_id: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    model_versions: Dict[str, str]

class InterpretationResult(BaseModel):
    category: str = Field(description="One of: 'Elevated concern', 'Mixed picture', 'Lower concern, under-evidenced', 'Insufficient basis'")
    summary: str = Field(description="Clear explanation of the overall evaluation")
    reasons: List[str] = Field(description="Documented conditions that triggered this interpretation")

class ReportSection(BaseModel):
    section_number: int
    title: str
    content: Dict[str, Any]

class EvaluationReport(BaseModel):
    meta: EvaluationMeta
    input_summary: Dict[str, Any]
    models: Dict[str, ModelEnvelope]
    interpretation: InterpretationResult
    key_factors: Dict[str, List[Dict[str, Any]]]
    trust: Dict[str, Any]
    issues: List[Dict[str, Any]]
    evidence_index: Dict[str, Any]
    sections: List[ReportSection]

class EvaluationStatusResponse(BaseModel):
    evaluation_id: str
    version: int = 1
    parent_id: Optional[str] = None
    status: str = Field(description="'queued', 'running', 'report_ready', 'complete', 'failed'")
    stage: str
    created_at: str
    completed_at: Optional[str] = None
    per_model_status: Dict[str, str]
    report_url: Optional[str] = None
    available_versions: List[Dict[str, Any]] = Field(default_factory=list)


