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
        if res_st.json()["status"] in ("report_ready", "complete"):
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

    # 3. Recommendations check
    res_rec = client.get(f"/v1/evaluations/{eval_id}/recommendations")
    assert res_rec.status_code == 200
    rec_body = res_rec.json()
    assert rec_body["status"] == "complete"
    assert len(rec_body["recommendations"]) > 0

    # 4. Export Endpoints (JSON, HTML, PDF)
    res_exp_json = client.get(f"/v1/evaluations/{eval_id}/export?format=json")
    assert res_exp_json.status_code == 200
    assert "application/json" in res_exp_json.headers["content-type"]
    assert eval_id in res_exp_json.text

    res_exp_html = client.get(f"/v1/evaluations/{eval_id}/export?format=html")
    assert res_exp_html.status_code == 200
    assert "text/html" in res_exp_html.headers["content-type"]
    assert "<html" in res_exp_html.text.lower()

    res_exp_pdf = client.get(f"/v1/evaluations/{eval_id}/export?format=pdf")
    assert res_exp_pdf.status_code == 200
    assert "application/pdf" in res_exp_pdf.headers["content-type"]
    assert res_exp_pdf.content.startswith(b"%PDF")

    # 5. Clarification Loop (Creates linked v2)
    clarif_payload = {
        "answers": [
            {
                "aspect": "Target Customer",
                "question": "What size fleets do you target?",
                "answer": "Tier-2 regional carriers operating between 50 and 150 class-8 freight trucks."
            },
            {
                "aspect": "Validation & Traction",
                "question": "What is the pilot contract status?",
                "answer": "12 active carrier pilots generating $35,000 in monthly recurring software fees."
            }
        ]
    }
    res_clarif = client.post(f"/v1/evaluations/{eval_id}/clarifications", json=clarif_payload)
    assert res_clarif.status_code == 202
    clarif_data = res_clarif.json()
    eval_id_v2 = clarif_data["evaluation_id"]
    assert clarif_data["parent_id"] == eval_id
    assert clarif_data["version"] == 2
    assert eval_id_v2 != eval_id

    # Verify v2 report status and lineage
    res_v2_st = client.get(f"/v1/evaluations/{eval_id_v2}")
    assert res_v2_st.status_code == 200
    st_data_v2 = res_v2_st.json()
    assert st_data_v2["version"] == 2
    assert st_data_v2["parent_id"] == eval_id
    assert len(st_data_v2["available_versions"]) == 2

    res_v2_rep = client.get(f"/v1/evaluations/{eval_id_v2}/report")
    assert res_v2_rep.status_code == 200

    # 6. Delete evaluation
    res_del = client.delete(f"/v1/evaluations/{eval_id}")
    assert res_del.status_code == 200
    assert res_del.json()["deleted"] is True

    # Check 404 after deletion
    res_not_found = client.get(f"/v1/evaluations/{eval_id}")
    assert res_not_found.status_code == 404


def test_model_fault_isolation_and_all_models_failed(client):
    from unittest.mock import patch
    from backend.schemas.envelope import ModelEnvelope

    # 1. Single model failure does not break the report run
    with patch("backend.adapters.model_c_adapter.ModelCAdapter.predict") as mock_c:
        mock_c.side_effect = RuntimeError("Simulated Model C CUDA out-of-memory error")

        payload = {
            "idea_description": "Robotic warehouse picking automation system with intelligent fleet scheduling.",
            "industry": "Artificial Intelligence / ML",
            "country": "USA",
            "funding_raised": 1000000.0,
            "funding_rounds": 1,
            "stage": "MVP",
            "consent": True
        }
        res = client.post("/v1/evaluations", json=payload)
        assert res.status_code == 202
        e_id = res.json()["evaluation_id"]

        st_res = client.get(f"/v1/evaluations/{e_id}")
        assert st_res.status_code == 200
        # Report still succeeded despite Model C failure
        assert st_res.json()["status"] in ("report_ready", "complete")
        assert st_res.json()["per_model_status"]["model_c"] == "error"

        rep_res = client.get(f"/v1/evaluations/{e_id}/report")
        assert rep_res.status_code == 200
        assert rep_res.json()["models"]["model_c"]["status"] == "error"

    # 2. All 4 models failing triggers failed status cleanly
    with patch("backend.orchestrator.Orchestrator.run_all_models") as mock_run:
        mock_run.return_value = {
            "model_a": ModelEnvelope(model_id="model_a", model_name="A", status="error", applicability_reason="fail"),
            "model_b": ModelEnvelope(model_id="model_b", model_name="B", status="error", applicability_reason="fail"),
            "model_c": ModelEnvelope(model_id="model_c", model_name="C", status="error", applicability_reason="fail"),
            "model_d": ModelEnvelope(model_id="model_d", model_name="D", status="error", applicability_reason="fail"),
        }
        res_all_fail = client.post("/v1/evaluations", json=payload)
        assert res_all_fail.status_code == 202
        fail_id = res_all_fail.json()["evaluation_id"]

        fail_st = client.get(f"/v1/evaluations/{fail_id}")
        assert fail_st.status_code == 200
        assert fail_st.json()["status"] == "failed"



