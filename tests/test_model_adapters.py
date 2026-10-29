"""Adapter contract tests for all four models."""
from pathlib import Path
import pytest
from backend.registry import registry

@pytest.fixture(scope="module", autouse=True)
def setup_registry():
    if not registry.is_ready:
        registry.load_all()

def test_model_a_adapter_contract():
    adapter = registry.get_adapter("model_a")
    assert adapter is not None

    # 1. Funded complete startup -> ok
    payload_ok = {
        "homepage_url": "https://example.com",
        "category_list": "Software|Enterprise",
        "funding_total_usd": 1000000.0,
        "country_code": "USA",
        "state_code": "CA",
        "region": "SF",
        "city": "SF",
        "funding_rounds": 1,
        "founded_at": "2020-01-01",
        "first_funding_at": "2020-06-01",
        "last_funding_at": "2020-06-01"
    }
    env_ok = adapter.predict(payload_ok)
    assert env_ok.status == "ok"
    assert "probabilities" in env_ok.data
    assert "top_contributing_features" in env_ok.data

    # 2. Pre-funding idea -> not_applicable (funding 0)
    payload_prefunding = dict(payload_ok, funding_total_usd=0.0, funding_rounds=0)
    env_prefunding = adapter.predict(payload_prefunding)
    assert env_prefunding.status == "not_applicable"
    assert "pre-funding" in env_prefunding.applicability_reason

    # 3. Missing dates -> not_applicable (dates missing)
    payload_no_dates = dict(payload_ok, founded_at=None, first_funding_at=None)
    env_no_dates = adapter.predict(payload_no_dates)
    assert env_no_dates.status == "not_applicable"
    assert "dates missing" in env_no_dates.applicability_reason

    # 4. Temporal warning when year > 2015
    payload_recent = dict(payload_ok, founded_at="2024-01-01", first_funding_at="2024-06-01", last_funding_at="2024-06-01")
    env_recent = adapter.predict(payload_recent)
    assert env_recent.status == "ok"
    assert any("2015" in w for w in env_recent.warnings)

def test_model_b_adapter_contract():
    adapter = registry.get_adapter("model_b")
    assert adapter is not None

    # 1. Funded startup -> ok
    payload_ok = {
        "category_code": "software",
        "state_code": "CA",
        "funding_total_usd": 2000000.0,
        "funding_rounds": 2,
        "has_VC": 1,
        "has_angel": 0,
        "has_roundA": 1,
        "has_roundB": 0,
        "has_roundC": 0,
        "has_roundD": 0
    }
    env_ok = adapter.predict(payload_ok)
    assert env_ok.status == "ok"
    assert 0 <= env_ok.data["risk_score"] <= 100
    assert env_ok.data["risk_level"] in ("Low", "Moderate", "High", "Very High")

    # 2. Pre-funding -> not_applicable
    payload_prefunding = dict(payload_ok, funding_total_usd=0.0, funding_rounds=0)
    env_pre = adapter.predict(payload_prefunding)
    assert env_pre.status == "not_applicable"
    assert "funded startups" in env_pre.applicability_reason

def test_model_c_adapter_contract():
    adapter = registry.get_adapter("model_c")
    assert adapter is not None

    # 1. Valid pitch -> ok
    payload_ok = {
        "idea_text": "AI platform that optimizes logistics and supply chains for warehouse operators.",
        "declared_sector": "AI",
        "extra": {"problem": "Manual tracking friction"}
    }
    env_ok = adapter.predict(payload_ok)
    assert env_ok.status == "ok"
    assert len(env_ok.data["aspect_findings"]) == 8
    assert "strengths" in env_ok.data

    # 2. Empty text -> not_applicable
    env_empty = adapter.predict({"idea_text": ""})
    assert env_empty.status == "not_applicable"

def test_model_d_adapter_contract():
    adapter = registry.get_adapter("model_d")
    assert adapter is not None

    # 1. Valid narrative -> ok
    payload_ok = {
        "text": "We ran a quick-commerce delivery platform with severe unit economics issues and collapsed inside a year.",
        "top_k_cases": 3
    }
    env_ok = adapter.predict(payload_ok)
    assert env_ok.status == "ok"
    assert len(env_ok.data["categories"]) == 8
    assert "predicted_categories" in env_ok.data
    assert "ood" in env_ok.data

    # 2. Empty text -> not_applicable
    env_empty = adapter.predict({"text": ""})
    assert env_empty.status == "not_applicable"



def test_adapter_edge_cases_and_null_safety():
    adapter_a = registry.get_adapter("model_a")
    adapter_b = registry.get_adapter("model_b")
    adapter_c = registry.get_adapter("model_c")
    adapter_d = registry.get_adapter("model_d")
    assert adapter_a is not None
    assert adapter_b is not None
    assert adapter_c is not None
    assert adapter_d is not None

    # 1. Null / None payloads
    assert adapter_a.predict(None).status in ("not_applicable", "error")
    assert adapter_b.predict(None).status in ("not_applicable", "error")
    assert adapter_c.predict(None).status in ("not_applicable", "error")
    assert adapter_d.predict(None).status in ("not_applicable", "error")

    # 2. Explicit None values in keys
    assert adapter_c.predict({"idea_text": None}).status == "not_applicable"
    assert adapter_c.predict({"idea_text": "Valid idea text", "extra": None}).status == "ok"
    assert adapter_d.predict({"text": None}).status == "not_applicable"
    assert adapter_d.predict({"text": "Valid text description for testing", "top_k_cases": None}).status == "ok"

    # 3. Invalid types in numeric fields
    assert adapter_a.predict({"funding_total_usd": "invalid", "funding_rounds": "bad"}).status == "not_applicable"
    assert adapter_b.predict({"funding_total_usd": "invalid", "funding_rounds": "bad"}).status == "not_applicable"

    # 4. Model B with missing optional flags
    payload_b_sparse = {
        "category_code": "software",
        "state_code": "CA",
        "funding_total_usd": 1000000.0,
        "funding_rounds": 1
    }
    env_b = adapter_b.predict(payload_b_sparse)
    assert env_b.status == "ok"
