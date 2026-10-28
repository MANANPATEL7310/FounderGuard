"""Schemas for recommendations, issues, and advisory output."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PrioritizedIssue(BaseModel):
    id: str
    theme: str
    title: str
    priority: str = Field(..., description="High, Medium, or Low")
    supporting_models: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    evidence_quotes: List[str] = Field(default_factory=list)
    confidence_note: str = ""
    is_gap_only: bool = False


class ClarifyingQuestion(BaseModel):
    question: str
    aspect: str
    reason_it_matters: str


class RecommendationItem(BaseModel):
    id: str
    issue_id: str
    identified_problem_or_risk: str
    why_it_matters_for_this_startup: str
    specific_action: str
    priority: str = Field(..., description="High, Medium, or Low; must equal assigned issue priority")
    implementation_steps: List[str]
    expected_benefit: str
    validation_method: str
    evidence_refs: List[str] = Field(default_factory=list)
    playbook_refs: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    evaluation_id: str
    status: str = "complete"
    generation_method: str = "template_playbook"
    is_fallback: bool = True
    disclaimer: str = (
        "Recommendations are prioritized suggestions based on historical failure patterns "
        "and provided pitch inputs. They do not guarantee success or prevent failure."
    )
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    other_observations: List[Dict[str, Any]] = Field(default_factory=list)
    clarifying_questions: List[ClarifyingQuestion] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
