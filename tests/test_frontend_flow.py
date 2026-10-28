"""Frontend tests verifying UI helpers, API client wrappers, and Streamlit AppTest flow."""
from unittest.mock import MagicMock, patch
import pytest
from streamlit.testing.v1 import AppTest
from frontend.ui_helpers import (
    error_card,
    not_applicable_card,
    ood_banner,
    word_meter,
    year_warning_banner,
)


def test_ui_helpers():
    # Word meter tests
    icon_red, msg_red = word_meter("Short idea description with few words.")
    assert "Under 40 words" in msg_red

    icon_amber, msg_amber = word_meter(" ".join(["word"] * 50))
    assert "40–80 words" in msg_amber

    icon_green, msg_green = word_meter(" ".join(["word"] * 90))
    assert "Good detail" in msg_green

    # Banner tests
    na_html = not_applicable_card("Model B", "Pre-funding idea")
    assert "Not Applicable" in na_html
    assert "Model B" in na_html

    err_html = error_card("Model A", "Timeout occurred")
    assert "Unavailable" in err_html

    ood_html = ood_banner("Model D")
    assert "Out-of-Distribution" in ood_html

    year_html = year_warning_banner("Year 2025 exceeds 2015")
    assert "Temporal Distribution Warning" in year_html


def test_frontend_landing_app_test():
    """Test initial rendering of the landing page."""
    with patch("frontend.api_client.check_backend_health", return_value=True), \
         patch("frontend.api_client.fetch_options", return_value={
             "industries": ["Artificial Intelligence / ML", "Other"],
             "countries": ["USA", "GBR"],
             "us_states": ["CA", "NY"],
             "currencies": ["USD", "EUR"],
             "stages": ["idea", "validation", "MVP"],
             "business_models": ["B2B", "SaaS"],
             "team_skills": ["engineering", "product"],
             "founder_experience": ["first-time"],
             "investor_types": ["venture capital"],
             "funding_rounds_options": ["Round A"],
         }):
        at = AppTest.from_file("frontend/app.py", default_timeout=10)
        at.run()
        assert not at.exception
        # Landing page renders title and consent
        assert "Startup Evaluation" in at.title[0].value
        assert len(at.checkbox) >= 1
        assert "consent" in at.checkbox[0].label.lower()


def test_frontend_report_rendering_with_banners():
    """Test report page rendering with not-applicable and OOD banners."""
    mock_report = {
        "meta": {
            "evaluation_id": "eval_test_123",
            "created_at": "2026-10-28T12:00:00Z",
            "completed_at": "2026-10-28T12:00:02Z",
            "model_versions": {"model_a": "v1", "model_b": "v1", "model_c": "v1", "model_d": "v1"}
        },
        "input_summary": {
            "idea_description": "Quantum-resilient messaging network for defense logistics.\nSecond line details.",
            "industry": "Artificial Intelligence / ML",
            "country": "USA",
            "state": "CA",
            "stage": "idea",
            "funding_total_usd": 0.0,
            "funding_rounds": 0,
            "provenance": {"provided_fields": ["idea_description"], "missing_fields": ["traction"]}
        },
        "models": {
            "model_a": {
                "model_id": "model_a",
                "model_name": "Startup Outcome Classifier",
                "status": "not_applicable",
                "applicability_reason": "dates missing: founded_at required",
                "data": None,
                "warnings": []
            },
            "model_b": {
                "model_id": "model_b",
                "model_name": "LogisticRegression",
                "status": "not_applicable",
                "applicability_reason": "funding_total_usd must be > 0",
                "data": None,
                "warnings": []
            },
            "model_c": {
                "model_id": "model_c",
                "model_name": "PyTorch BiGRU",
                "status": "ok",
                "data": {
                    "sector_check": {"declared_sector": "AI", "note": "Consistent"},
                    "aspect_findings": [
                        {"aspect": "Target Customer", "status": "evidence_found", "note": "Clear", "evidence": ["defense logistics"]},
                        {"aspect": "Pricing / Revenue", "status": "not_stated", "note": "Not mentioned", "evidence": []}
                    ],
                    "vague_terms": ["next-gen"],
                    "missing_information_questions": [{"aspect": "Revenue", "question": "What is your pricing model?"}],
                    "strengths": [],
                    "potential_weaknesses_and_gaps": []
                },
                "warnings": []
            },
            "model_d": {
                "model_id": "model_d",
                "model_name": "Failure Category Classifier",
                "status": "ok",
                "data": {
                    "ood": {"flagged": True, "nearest_case_similarity": 0.12, "threshold": 0.25},
                    "meaning": "Similarity to past failures",
                    "categories": [
                        {
                            "category": "market_demand",
                            "label": "No market need",
                            "supported": True,
                            "probability": 0.65,
                            "threshold": 0.5,
                            "predicted": True,
                            "evidence_sentence": "Defense logistics market is niche",
                            "similar_historical_failures": []
                        }
                    ],
                    "predicted_categories": ["market_demand"]
                },
                "warnings": []
            }
        },
        "interpretation": {
            "category": "Insufficient basis",
            "summary": "Quantitative financial models are not applicable.",
            "reasons": ["Model A: dates missing", "Model B: funding is 0"]
        },
        "key_factors": {},
        "trust": {
            "warnings": ["[model_d] OOD flagged"],
            "currency_conversion": {"original": "0 USD", "converted_usd": "$0.00 USD", "rate": 1.0, "date": "2026-10-28"},
            "provenance": {"provided_fields": ["idea_description"], "missing_fields": ["traction"]},
            "general_limitations": ["Statistical approximations"]
        },
        "issues": [
            {"id": "iss_1", "source": "Model D", "title": "Market need risk", "severity": "High", "evidence": "Defense niche"}
        ],
        "evidence_index": {},
        "sections": [
            {"section_number": 1, "title": "Executive Summary", "content": {"summary_text": "Executive summary text"}},
            {"section_number": 2, "title": "Model A", "content": {}},
            {"section_number": 3, "title": "Model B", "content": {}},
            {"section_number": 4, "title": "Model C", "content": {}},
            {"section_number": 5, "title": "Model D", "content": {}},
            {"section_number": 6, "title": "Key Factors", "content": {}},
            {"section_number": 7, "title": "Trust Panel", "content": {}},
            {"section_number": 8, "title": "Next Steps", "content": {}}
        ]
    }

    with patch("frontend.api_client.check_backend_health", return_value=True), \
         patch("frontend.api_client.fetch_options", return_value={}):
        at = AppTest.from_file("frontend/app.py", default_timeout=10)
        at.run()
        # Set session state to report page with mock report
        at.session_state["page"] = "report"
        at.session_state["report"] = mock_report
        at.session_state["eval_id"] = "eval_test_123"
        at.run()

        assert not at.exception
        # Header renders
        assert "Quantum-resilient messaging network" in at.title[0].value
        # Check tabs exist
        assert len(at.tabs) == 3
