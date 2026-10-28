"""Integration tests for FastAPI endpoints."""
import time
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.registry import registry

@pytest.fixture(scope="module")
def client():
    if not registry.is_ready:
        registry.load_all()
    with TestClient(app) as c:
        yield c

def test_health_and_ready(client):
    res_h = client.get("/health")
    assert res_h.status_code == 200
    assert res_h.json()["status"] == "ok"

    res_r = client.get("/ready")
    assert res_r.status_code == 200
    assert res_r.json()["status"] == "ready"

def test_meta_options(client):
    res = client.get("/v1/meta/options")
    assert res.status_code == 200
    data = res.json()
    assert len(data["industries"]) > 0
    assert len(data["countries"]) > 0
    assert "USD" in data["currencies"]

def test_models_catalog(client):
    res = client.get("/v1/models")
    assert res.status_code == 200
    data = res.json()
    assert "model_a" in data["models"]
    assert "model_b" in data["models"]
    assert "model_c" in data["models"]
    assert "model_d" in data["models"]

def test_validate_endpoint_funded_vs_prefunding(client):
    # Funded US startup
    payload_funded = {
        "idea_description": "Building automated picking robots for e-commerce fulfillment warehouses.",
        "industry": "Artificial Intelligence / ML",
        "country": "USA",
        "state": "CA",
        "stage": "MVP",
        "funding_raised": 1500000.0,
        "currency": "USD",
        "funding_rounds": 1,
        "investor_types": ["venture capital"],
        "rounds_reached": ["Round A"],
        "founded_at": "2021-01-01",
        "first_funding_at": "2021-06-01",
        "last_funding_at": "2021-06-01",
        "consent": True
    }
    res = client.post("/v1/evaluations/validate", json=payload_funded)
    assert res.status_code == 200
    val_data = res.json()
    assert val_data["valid"] is True
    assert val_data["models_applicability"]["model_a"]["applicable"] is True
    assert val_data["models_applicability"]["model_b"]["applicable"] is True
    assert val_data["models_applicability"]["model_c"]["applicable"] is True
    assert val_data["models_applicability"]["model_d"]["applicable"] is True

    # Pre-funding idea
    payload_pre = dict(payload_funded, funding_raised=0.0, funding_rounds=0, founded_at=None, first_funding_at=None, last_funding_at=None)
    res_pre = client.post("/v1/evaluations/validate", json=payload_pre)
    assert res_pre.status_code == 200
    val_pre_data = res_pre.json()
    assert val_pre_data["models_applicability"]["model_a"]["applicable"] is False
    assert val_pre_data["models_applicability"]["model_b"]["applicable"] is False
    assert val_pre_data["models_applicability"]["model_c"]["applicable"] is True
    assert val_pre_data["models_applicability"]["model_d"]["applicable"] is True

def test_submit_and_fetch_report(client):
    payload = {
        "idea_description": "Real-time AI logistics optimization engine reducing empty backhauls for freight fleets.",
        "problem_statement": "Trucks run empty on 25% of return legs, wasting fuel and operational margin.",
        "target_customer": "Regional mid-sized freight carriers with 20 to 100 trucks.",
        "industry": "Transportation, Logistics & Supply Chain",
        "country": "USA",
        "state": "TX",
        "business_model": ["B2B", "SaaS"],
        "stage": "launched",
        "funding_raised": 2000000.0,
        "currency": "USD",
        "funding_rounds": 1,
        "investor_types": ["venture capital"],
        "rounds_reached": ["Round A"],
        "team_size": 6,
        "team_skills": ["engineering", "operations"],
        "founder_experience": "prior startup",
        "validation_evidence": "12 signed fleet pilot agreements operating weekly.",
        "founded_at": "2021-03-01",
        "first_funding_at": "2021-08-01",
        "last_funding_at": "2021-08-01",
        "consent": True
    }
    # 1. Submit
    res_sub = client.post("/v1/evaluations", json=payload)
    assert res_sub.status_code == 202
    eval_id = res_sub.json()["evaluation_id"]

    # 2. Wait for completion (sync test client runs background tasks before returning or quickly)
    report_data = None
    for _ in range(10):
        res_st = client.get(f"/v1/evaluations/{eval_id}")
        if res_st.json()["status"] == "report_ready":
            res_rep = client.get(f"/v1/evaluations/{eval_id}/report")
            assert res_rep.status_code == 200
            report_data = res_rep.json()
            break
        time.sleep(0.5)

    assert report_data is not None, "Report did not become ready"
    assert "sections" in report_data
    assert len(report_data["sections"]) == 8
    assert report_data["models"]["model_a"]["status"] == "ok"
    assert report_data["models"]["model_b"]["status"] == "ok"
    assert report_data["models"]["model_c"]["status"] == "ok"
    assert report_data["models"]["model_d"]["status"] == "ok"
    assert report_data["interpretation"]["category"] in [
        "Elevated concern", "Mixed picture", "Lower concern, under-evidenced", "Insufficient basis"
    ]

    # 3. Recommendations stub check
    res_rec = client.get(f"/v1/evaluations/{eval_id}/recommendations")
    assert res_rec.status_code == 200
    assert res_rec.json()["status"] == "coming_soon"

    # 4. Delete evaluation
    res_del = client.delete(f"/v1/evaluations/{eval_id}")
    assert res_del.status_code == 200
    assert res_del.json()["deleted"] is True
