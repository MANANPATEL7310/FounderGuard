"""Unit tests for normalization, mapping tables, and text composition."""
import pytest
from backend.normalization.currency import convert_to_usd
from backend.normalization.industry import AVAILABLE_INDUSTRIES, INDUSTRY_MAPPING, map_industry
from backend.normalization.locations import normalize_location
from backend.normalization.normalizer import Normalizer
from backend.schemas.submission import SubmissionInput

def test_currency_conversion():
    val, rate, date_str = convert_to_usd(1000.0, "EUR")
    assert val == 1080.0
    assert rate == 1.08
    assert date_str == "2026-10-28"

    val_usd, rate_usd, _ = convert_to_usd(500.0, "USD")
    assert val_usd == 500.0
    assert rate_usd == 1.0

def test_all_industries_mapped_to_valid_categories():
    for ind in AVAILABLE_INDUSTRIES:
        b_cat, c_sec, a_cat = map_industry(ind)
        assert b_cat is not None and len(b_cat) > 0
        assert c_sec is not None and len(c_sec) > 0
        assert a_cat is not None and len(a_cat) > 0

def test_locations_normalization():
    country, state, b_state, is_us = normalize_location("USA", "CA")
    assert country == "USA"
    assert state == "CA"
    assert b_state == "CA"
    assert is_us is True

    country, state, b_state, is_us = normalize_location("USA", "WA")
    assert country == "USA"
    assert state == "WA"
    assert b_state == "OTHER"
    assert is_us is True

    country, state, b_state, is_us = normalize_location("GBR", None)
    assert country == "GBR"
    assert b_state == "OTHER"
    assert is_us is False

def test_normalizer_pipeline():
    sub = SubmissionInput(
        idea_description="We are building an <b>AI-driven</b> autonomous warehouse robotics platform.",
        problem_statement="Warehouses lose 30% of inventory efficiency due to manual picking errors.",
        target_customer="Warehouse managers and 3PL fulfillment operators.",
        industry="Artificial Intelligence / ML",
        country="USA",
        state="CA",
        business_model=["B2B", "SaaS"],
        stage="MVP",
        funding_raised=2500000.0,
        currency="USD",
        funding_rounds=2,
        investor_types=["venture capital", "angel"],
        rounds_reached=["Round A"],
        team_size=5,
        team_skills=["engineering", "product"],
        founder_experience="prior startup",
        validation_evidence="3 pilot contracts signed.",
        homepage_url="https://robo-pick.ai",
        city="San Jose",
        region="Silicon Valley",
        founded_at="2022-01-01",
        first_funding_at="2022-06-01",
        last_funding_at="2023-01-01",
    )

    norm, warnings = Normalizer.normalize(sub)
    assert "<b>" not in norm["idea_description"]
    assert norm["funding_total_usd"] == 2500000.0
    assert norm["model_b_payload"]["has_VC"] == 1
    assert norm["model_b_payload"]["has_angel"] == 1
    assert norm["model_b_payload"]["has_roundA"] == 1
    assert norm["model_b_payload"]["has_roundB"] == 0
    assert norm["model_c_payload"]["declared_sector"] == "AI"
    assert "problem" in norm["model_c_payload"]["extra"]
    assert "robotics" in norm["model_d_payload"]["text"].lower()
    # Model D text should not contain negative filler
    assert "no customers" not in norm["model_d_payload"]["text"].lower()
    assert "idea_description" in norm["provenance"]["provided_fields"]
    assert "competitors" in norm["provenance"]["missing_fields"]
