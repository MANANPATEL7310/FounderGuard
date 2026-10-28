"""Unit tests for the Issue Prioritizer and priority rules (Section 5.4)."""
import pytest
from backend.recommendations.engine import RecommendationEngine
from backend.recommendations.prioritizer import IssuePrioritizer
from backend.schemas.envelope import ModelEnvelope


def _make_envelope(model_id: str, status: str = "ok", data: dict = None) -> ModelEnvelope:
    return ModelEnvelope(
        model_id=model_id,
        model_name=f"Test {model_id}",
        status=status,
        data=data or {},
        warnings=[],
        runtime_ms=10.0,
    )


def test_priority_rules_multi_model_support_yields_high():
    """Rule 1: Theme supported by 2 or more different models must be assigned High priority."""
    envelopes = {
        "model_d": _make_envelope("model_d", data={
            "ood": {"flagged": False},
            "categories": [
                {
                    "category": "unit_economics_pricing",
                    "label": "Poor unit economics or pricing",
                    "supported": True,
                    "probability": 0.45,  # Moderate prob on D
                    "threshold": 0.50,
                    "predicted": False,
                    "evidence_sentence": "Couriers were subsidized heavily.",
                }
            ],
            "predicted_categories": [],
        }),
        "model_c": _make_envelope("model_c", data={
            "aspect_findings": [
                {
                    "aspect": "Business Model & Pricing",
                    "status": "not_stated",
                    "note": "Pricing mechanics omitted.",
                }
            ],
            "vague_terms": [],
            "missing_information_questions": [],
        }),
    }

    top_issues, other_obs = IssuePrioritizer.prioritize_issues(
        envelopes=envelopes,
        normalized={"stage": "MVP", "industry": "Technology"},
    )

    issue_map = {iss.theme: iss for iss in top_issues}
    assert "unit_economics_pricing" in issue_map
    pricing_issue = issue_map["unit_economics_pricing"]
    assert pricing_issue.priority == "High"
    assert set(pricing_issue.supporting_models) == {"model_c", "model_d"}


def test_priority_rules_model_d_predicted_yields_high():
    """Rule 1: Model D predicted category (predicted=True) gets High priority."""
    envelopes = {
        "model_d": _make_envelope("model_d", data={
            "ood": {"flagged": False},
            "categories": [
                {
                    "category": "market_demand",
                    "label": "No market need",
                    "supported": True,
                    "probability": 0.72,
                    "threshold": 0.50,
                    "predicted": True,
                    "label_quality": "acceptable",
                    "evidence_sentence": "Nobody wanted this product.",
                }
            ],
            "predicted_categories": ["market_demand"],
        }),
    }

    top_issues, _ = IssuePrioritizer.prioritize_issues(
        envelopes=envelopes,
        normalized={"stage": "idea", "industry": "Technology"},
    )

    issue_map = {iss.theme: iss for iss in top_issues}
    assert "market_demand" in issue_map
    assert issue_map["market_demand"].priority == "High"


def test_priority_rules_model_b_high_risk_yields_high():
    """Rule 1: Model B risk level High or Very High assigns High priority to funding_cashflow."""
    envelopes = {
        "model_b": _make_envelope("model_b", data={
            "risk_score": 78.5,
            "risk_level": "Very High",
            "meaning": "High relative failure probability among US funded startups.",
            "top_contributing_features": [
                {"feature": "funding_total_usd", "value": "50000", "direction": "raises", "effect_on_probability": 0.15}
            ],
        }),
    }

    top_issues, _ = IssuePrioritizer.prioritize_issues(
        envelopes=envelopes,
        normalized={"stage": "launched", "industry": "SaaS"},
    )

    issue_map = {iss.theme: iss for iss in top_issues}
    assert "funding_cashflow" in issue_map
    assert issue_map["funding_cashflow"].priority == "High"


def test_priority_rules_ood_capping_to_medium():
    """Rule 2: If Model D OOD is flagged, issues supported ONLY by Model D are capped at Medium."""
    envelopes = {
        "model_d": _make_envelope("model_d", data={
            "ood": {"flagged": True, "nearest_case_similarity": 0.08, "threshold": 0.25},
            "categories": [
                {
                    "category": "competition_differentiation",
                    "label": "Outcompeted",
                    "supported": True,
                    "probability": 0.85,
                    "threshold": 0.50,
                    "predicted": True,  # would be High if not OOD
                    "label_quality": "acceptable",
                    "evidence_sentence": "Incumbents crushed us.",
                }
            ],
            "predicted_categories": ["competition_differentiation"],
        }),
    }

    top_issues, _ = IssuePrioritizer.prioritize_issues(
        envelopes=envelopes,
        normalized={"stage": "validation", "industry": "Consumer"},
    )

    issue_map = {iss.theme: iss for iss in top_issues}
    assert "competition_differentiation" in issue_map
    # MUST be capped at Medium due to OOD
    assert issue_map["competition_differentiation"].priority == "Medium"
    assert "out-of-distribution" in issue_map["competition_differentiation"].confidence_note.lower()


def test_priority_rules_ood_not_capped_if_multi_model():
    """If Model D OOD is flagged, but another model also supports the theme, it remains High."""
    envelopes = {
        "model_d": _make_envelope("model_d", data={
            "ood": {"flagged": True},
            "categories": [
                {
                    "category": "competition_differentiation",
                    "label": "Outcompeted",
                    "supported": True,
                    "probability": 0.85,
                    "threshold": 0.50,
                    "predicted": True,
                    "label_quality": "acceptable",
                    "evidence_sentence": "Incumbents crushed us.",
                }
            ],
            "predicted_categories": ["competition_differentiation"],
        }),
        "model_c": _make_envelope("model_c", data={
            "aspect_findings": [
                {
                    "aspect": "Competitors & Differentiation",
                    "status": "not_stated",
                    "note": "No direct competitors named.",
                }
            ],
            "vague_terms": [],
            "missing_information_questions": [],
        }),
    }

    top_issues, _ = IssuePrioritizer.prioritize_issues(
        envelopes=envelopes,
        normalized={"stage": "validation", "industry": "Consumer"},
    )

    issue_map = {iss.theme: iss for iss in top_issues}
    assert "competition_differentiation" in issue_map
    # Multi-model overrides OOD single-model cap
    assert issue_map["competition_differentiation"].priority == "High"


def test_priority_rules_single_gap_only_yields_low():
    """Rule 3: Only weak single 'not stated' gaps without corroboration get Low priority."""
    envelopes = {
        "model_c": _make_envelope("model_c", data={
            "aspect_findings": [
                {
                    "aspect": "Target Customer",
                    "status": "not_stated",
                    "note": "No specific buyer profile detailed.",
                }
            ],
            "vague_terms": [],
            "missing_information_questions": [],
        }),
    }

    top_issues, _ = IssuePrioritizer.prioritize_issues(
        envelopes=envelopes,
        normalized={"stage": "idea", "industry": "Other"},
    )

    issue_map = {iss.theme: iss for iss in top_issues}
    assert "acquisition_retention" in issue_map
    assert issue_map["acquisition_retention"].priority == "Low"


def test_recommendation_engine_full_schema_consistency():
    """Test that RecommendationEngine generates valid items with exact priority parity."""
    envelopes = {
        "model_d": _make_envelope("model_d", data={
            "ood": {"flagged": False},
            "categories": [
                {
                    "category": "market_demand",
                    "label": "No market need",
                    "supported": True,
                    "probability": 0.70,
                    "threshold": 0.50,
                    "predicted": True,
                    "evidence_sentence": "Low buyer interest observed.",
                }
            ],
            "predicted_categories": ["market_demand"],
        }),
        "model_c": _make_envelope("model_c", data={
            "aspect_findings": [
                {"aspect": "Customer Demand Validation", "status": "not_stated", "note": "No interviews cited."}
            ],
            "vague_terms": ["disruptive"],
            "missing_information_questions": [
                {"aspect": "Validation", "question": "Have you conducted customer interviews?"}
            ],
        }),
    }

    resp = RecommendationEngine.generate(
        evaluation_id="eval_test_recs",
        normalized={"stage": "idea", "industry": "FinTech", "idea_description": "A payment app for teenagers."},
        envelopes=envelopes,
    )

    assert resp.status == "complete"
    assert resp.is_fallback is True
    assert len(resp.recommendations) > 0

    for rec in resp.recommendations:
        # 7 plan fields must be present and non-empty
        assert rec.id
        assert rec.issue_id
        assert rec.identified_problem_or_risk
        assert rec.why_it_matters_for_this_startup
        assert rec.specific_action
        assert rec.priority in ("High", "Medium", "Low")
        assert len(rec.implementation_steps) >= 3
        assert rec.expected_benefit
        assert rec.validation_method
        assert len(rec.playbook_refs) >= 1
        assert "guarantee" not in rec.expected_benefit.lower()

    # Clarifying questions attached
    assert len(resp.clarifying_questions) >= 1
    assert "interviews" in resp.clarifying_questions[0].question.lower()
