"""Schema for dropdown metadata and options."""
from pydantic import BaseModel, Field
from typing import List, Dict

class OptionsResponse(BaseModel):
    industries: List[str] = Field(description="Available industry sectors")
    countries: List[Dict[str, str]] = Field(description="List of {code, name}")
    us_states: List[Dict[str, str]] = Field(description="List of {code, name} for US states")
    currencies: List[str] = Field(description="Supported currency codes")
    stages: List[str] = Field(description="Current startup development stages")
    business_models: List[str] = Field(description="Available business models")
    team_skills: List[str] = Field(description="Recognized team skill sets")
    founder_experience: List[str] = Field(description="Founder background categories")
    investor_types: List[str] = Field(description="Investor types")
    funding_rounds_options: List[str] = Field(description="Funding round milestones reached")
    field_limits: Dict[str, int] = Field(description="Character and value constraints")
