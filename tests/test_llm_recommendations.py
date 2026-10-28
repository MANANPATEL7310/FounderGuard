"""Unit tests for Step 4: Open-Source LLM Recommendation Client, Validator, Grounding, and Cache."""
import json
import pytest
from unittest.mock import MagicMock, patch

from backend.recommendations.grounding import GroundingPackBuilder
from backend.recommendations.llm_client import LLMClient
from backend.recommendations.validator import RecommendationValidator
from backend.schemas.envelope import ModelEnvelope
from backend.schemas.recommendation import PrioritizedIssue, RecommendationResponse


@pytest.fixture
def sample_grounding_pack():
    return {
        "evaluation_id": "test_eval_123",
        "user_profile": {
            "industry": "Artificial Intelligence / ML",
            "stage": "idea",
            "country": "USA",
        },
        "model_digest": {
            "model_b": {"status": "ok", "risk_level": "High"},
            "model_d": {"status": "ok", "predicted_categories": ["funding_cashflow"]},
        },
        "prioritized_issues": [
            {
                "id": "issue_1",
                "theme": "funding_cashflow",
                "title": "Capital Runway & Cash-Flow Sustainability",
                "priority": "High",
                "evidence_refs": ["b_financial_risk"],
            }
        ],
        "evidence_index": {
            "b_financial_risk": "Model B assessed failure risk at 75/100",
        },
        "playbook_excerpts": [
            {
                "id": "pb_cashflow",
                "theme": "funding_cashflow",
                "title": "18-Month Runway Plan",
                "action": "Build a rolling cashflow forecast.",
            }
        ],
    }


def test_validator_accepts_valid_json_matching_grounding(sample_grounding_pack):
    valid_llm_output = json.dumps({
        "recommendations": [
            {
                "id": "rec_1",
                "issue_id": "issue_1",
                "identified_problem_or_risk": "Capital Runway & Cash-Flow Sustainability",
                "why_it_matters_for_this_startup": "Early stage AI companies burn capital quickly without milestone-based budgeting.",
                "specific_action": "Build a monthly zero-based cashflow model tracking runway.",
                "priority": "High",
                "implementation_steps": [
                    "Audit current fixed and variable monthly commitments.",
                    "Set minimum target threshold of 9 months buffer.",
                    "Tie future hiring decisions to revenue inflection metrics.",
                ],
                "expected_benefit": "Prevents sudden cash depletion and improves investor confidence.",
                "validation_method": "Maintain runway above 9 months over the next 2 quarters.",
                "evidence_refs": ["b_financial_risk"],
                "playbook_refs": ["pb_cashflow"],
                "assumptions": ["Founders have visibility into bank transactions."],
            }
        ],
        "clarifying_questions": [
            {
                "question": "What is the expected monthly cloud compute spend?",
                "aspect": "Financial Runway",
                "reason_it_matters": "GPU infrastructure can drastically alter burn rate.",
            }
        ],
        "assumptions": ["Recommendations assume US market conditions."],
    })

    is_valid, errors, response = RecommendationValidator.validate(valid_llm_output, sample_grounding_pack)
    assert is_valid is True
    assert len(errors) == 0
    assert response is not None
    assert len(response.recommendations) == 1
    assert response.recommendations[0].priority == "High"


def test_validator_rejects_priority_mismatch(sample_grounding_pack):
    output_with_wrong_priority = json.dumps({
        "recommendations": [
            {
                "id": "rec_1",
                "issue_id": "issue_1",
                "identified_problem_or_risk": "Capital Runway",
                "why_it_matters_for_this_startup": "Runway is low.",
                "specific_action": "Cut expenses.",
                "priority": "Low",  # Should be High!
                "implementation_steps": ["Step 1", "Step 2", "Step 3"],
                "expected_benefit": "Saves cash.",
                "validation_method": "Check balance in 30 days.",
                "evidence_refs": ["b_financial_risk"],
            }
        ]
    })

    is_valid, errors, _ = RecommendationValidator.validate(output_with_wrong_priority, sample_grounding_pack)
    assert is_valid is False
    assert any("does not match assigned issue priority" in e for e in errors)


def test_validator_rejects_prohibited_guarantee_phrases(sample_grounding_pack):
    output_with_guarantee = json.dumps({
        "recommendations": [
            {
                "id": "rec_1",
                "issue_id": "issue_1",
                "identified_problem_or_risk": "Capital Runway",
                "why_it_matters_for_this_startup": "Runway is critical.",
                "specific_action": "Apply this strategy.",
                "priority": "High",
                "implementation_steps": ["Step 1", "Step 2", "Step 3"],
                "expected_benefit": "This action will guarantee success and ensure 100% chance of survival.",
                "validation_method": "Check balance.",
                "evidence_refs": ["b_financial_risk"],
            }
        ]
    })

    is_valid, errors, _ = RecommendationValidator.validate(output_with_guarantee, sample_grounding_pack)
    assert is_valid is False
    assert any("prohibited claim or guarantee pattern" in e for e in errors)


def test_validator_rejects_ungrounded_evidence_reference(sample_grounding_pack):
    output_with_invented_ref = json.dumps({
        "recommendations": [
            {
                "id": "rec_1",
                "issue_id": "issue_1",
                "identified_problem_or_risk": "Capital Runway",
                "why_it_matters_for_this_startup": "Runway is critical.",
                "specific_action": "Apply this strategy.",
                "priority": "High",
                "implementation_steps": ["Step 1", "Step 2", "Step 3"],
                "expected_benefit": "Improves runway.",
                "validation_method": "Check balance.",
                "evidence_refs": ["invented_hallucinated_ref_999"],
            }
        ]
    })

    is_valid, errors, _ = RecommendationValidator.validate(output_with_invented_ref, sample_grounding_pack)
    assert is_valid is False
    assert any("not found in grounding pack" in e for e in errors)


def test_llm_client_repair_flow(sample_grounding_pack):
    client = LLMClient()

    # First response fails (priority mismatch); repaired response passes
    bad_output = json.dumps({
        "recommendations": [
            {
                "id": "rec_1",
                "issue_id": "issue_1",
                "identified_problem_or_risk": "Capital Runway",
                "why_it_matters_for_this_startup": "Runway",
                "specific_action": "Forecast cashflow",
                "priority": "Low",  # Wrong
                "implementation_steps": ["Step 1", "Step 2", "Step 3"],
                "expected_benefit": "Better planning",
                "validation_method": "Check monthly",
                "evidence_refs": ["b_financial_risk"],
            }
        ]
    })

    good_output = json.dumps({
        "recommendations": [
            {
                "id": "rec_1",
                "issue_id": "issue_1",
                "identified_problem_or_risk": "Capital Runway",
                "why_it_matters_for_this_startup": "Runway",
                "specific_action": "Forecast cashflow",
                "priority": "High",  # Repaired!
                "implementation_steps": ["Step 1", "Step 2", "Step 3"],
                "expected_benefit": "Better planning",
                "validation_method": "Check monthly",
                "evidence_refs": ["b_financial_risk"],
            }
        ]
    })

    mock_resp_1 = MagicMock()
    mock_resp_1.status_code = 200
    mock_resp_1.json.return_value = {"choices": [{"message": {"content": bad_output}}]}

    mock_resp_2 = MagicMock()
    mock_resp_2.status_code = 200
    mock_resp_2.json.return_value = {"choices": [{"message": {"content": good_output}}]}

    with patch("httpx.Client.post", side_effect=[mock_resp_1, mock_resp_2]):
        with patch("backend.recommendations.llm_client.LLM_MODEL", "test-model"):
            with patch("backend.recommendations.llm_client.ENABLE_LLM", True):
                result = client.generate_recommendations(sample_grounding_pack)
                assert result is not None
                assert result.generation_method == "llm_repaired"
                assert result.recommendations[0].priority == "High"


def test_llm_client_caching(sample_grounding_pack):
    client = LLMClient()
    good_output = json.dumps({
        "recommendations": [
            {
                "id": "rec_1",
                "issue_id": "issue_1",
                "identified_problem_or_risk": "Capital Runway",
                "why_it_matters_for_this_startup": "Runway",
                "specific_action": "Forecast cashflow",
                "priority": "High",
                "implementation_steps": ["Step 1", "Step 2", "Step 3"],
                "expected_benefit": "Better planning",
                "validation_method": "Check monthly",
                "evidence_refs": ["b_financial_risk"],
            }
        ]
    })

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": [{"message": {"content": good_output}}]}

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        with patch("backend.recommendations.llm_client.LLM_MODEL", "test-model"):
            with patch("backend.recommendations.llm_client.ENABLE_LLM", True):
                # Call 1: makes network call
                res1 = client.generate_recommendations(sample_grounding_pack)
                assert res1 is not None
                assert mock_post.call_count == 1

                # Call 2 with identical input: served from memory cache (call count stays 1)
                res2 = client.generate_recommendations(sample_grounding_pack)
                assert res2 is not None
                assert mock_post.call_count == 1
