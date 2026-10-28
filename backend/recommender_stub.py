"""Recommender stub for Step 1."""
from typing import Any, Dict

def get_recommendations_stub(evaluation_id: str) -> Dict[str, Any]:
    return {
        "evaluation_id": evaluation_id,
        "status": "coming_soon",
        "items": [],
        "note": "Recommendation engine will be activated in Step 3 (playbook rules) and Step 4 (LLM).",
    }
