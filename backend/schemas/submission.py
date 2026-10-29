"""Schemas for startup submission and validation."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

class SubmissionInput(BaseModel):
    # Core Pitch (Feeds C, D, LLM)
    idea_description: str = Field(..., min_length=20, max_length=4000, description="Detailed idea pitch")
    problem_statement: Optional[str] = Field(default=None, max_length=1000, description="Problem being solved")
    target_customer: Optional[str] = Field(default=None, max_length=500, description="Target customer segment")
    
    # Classification & Location (Feeds A, B, C, LLM)
    industry: str = Field(..., description="Industry or sector dropdown selection")
    country: str = Field(..., description="Country code (e.g. USA, GBR, IND, CAN)")
    state: Optional[str] = Field(default=None, description="US State code if country is USA")
    target_market: str = Field(default="global", description="Market scope: local, national, regional, global")
    business_model: List[str] = Field(default_factory=list, description="Business models: B2B, B2C, SaaS, etc.")
    stage: str = Field(default="idea", description="Stage: idea, validation, MVP, launched, growing")
    
    # Financials (Feeds A, B)
    budget_available: Optional[float] = Field(default=None, ge=0, description="Self-reported operational budget")
    funding_raised: float = Field(default=0.0, ge=0, description="Total equity/debt funding raised so far in declared currency")
    currency: str = Field(default="USD", description="Currency code (e.g. USD, EUR, GBP, INR)")
    funding_rounds: int = Field(default=0, ge=0, description="Number of formal investment rounds closed")
    investor_types: List[str] = Field(default_factory=list, description="Investor types: venture capital, angel, none")
    rounds_reached: List[str] = Field(default_factory=list, description="Milestone rounds: Round A, B, C, D, none")
    
    # Team & Founder (Feeds D text & LLM)
    team_size: int = Field(default=1, ge=1, le=500, description="Current full-time/core team members")
    team_skills: List[str] = Field(default_factory=list, description="Core skills present in team")
    founder_experience: str = Field(default="first-time", description="Experience level: first-time, prior startup, prior exit, domain veteran")
    
    # Validation & Traction (Feeds C extra, D text, LLM)
    validation_evidence: Optional[str] = Field(default=None, max_length=1000, description="Customer interviews, LOIs, pilots, surveys")
    competitors: Optional[str] = Field(default=None, max_length=1000, description="Known competitors or substitutes")
    traction: Optional[str] = Field(default=None, max_length=1000, description="Paying users, revenue, active pilots, retention")
    
    # Optional Details for Model A
    homepage_url: Optional[str] = Field(default=None, description="Website or landing page URL")
    city: Optional[str] = Field(default=None, description="Headquarters city")
    region: Optional[str] = Field(default=None, description="Geographic region / metro area")
    founded_at: Optional[str] = Field(default=None, description="Founding date (YYYY-MM-DD)")
    first_funding_at: Optional[str] = Field(default=None, description="Date of first funding round (YYYY-MM-DD)")
    last_funding_at: Optional[str] = Field(default=None, description="Date of most recent funding round (YYYY-MM-DD)")
    
    # Compliance Gate
    consent: bool = Field(default=True, description="User consent to evaluate and process submission")

    @field_validator("funding_raised", "funding_rounds", mode="before")
    def coerce_numbers(cls, v):
        if v is None:
            return 0
        return v

class NormalizedSummary(BaseModel):
    idea_description: str
    industry: str
    country: str
    state: Optional[str]
    funding_total_usd: float
    funding_rounds: int
    exchange_rate_used: float
    exchange_rate_date: str
    original_funding: float
    original_currency: str
    stage: str
    provenance_provided_fields: List[str]
    provenance_missing_fields: List[str]

class ValidateResponse(BaseModel):
    valid: bool
    normalized: NormalizedSummary
    models_applicability: Dict[str, Dict[str, Any]]
    warnings: List[str]

class SubmissionResponse(BaseModel):
    evaluation_id: str
    status: str
    created_at: str
    check_status_url: str


class ClarificationAnswer(BaseModel):
    aspect: str
    question: str
    answer: str


class ClarificationRequest(BaseModel):
    answers: List[ClarificationAnswer]


class ClarificationResponse(BaseModel):
    evaluation_id: str
    parent_id: str
    version: int
    status: str
    created_at: str
    check_status_url: str


