"""Concurrency and load tests fulfilling Section 4.12."""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def test_concurrent_evaluations_load(client):
    """
    Simulates 8 concurrent users submitting evaluations simultaneously.
    Verifies thread-safety, non-overlapping evaluation IDs, and full report generation.
    """
    concurrent_requests = 8

    def _submit_single(index: int):
        payload = {
            "idea_description": f"Autonomous micro-fulfillment system number {index} with robotics and AI sorting.",
            "industry": "Artificial Intelligence / ML",
            "country": "USA",
            "state": "CA",
            "stage": "MVP",
            "funding_raised": 500000.0 * (index + 1),
            "funding_rounds": 1,
            "currency": "USD",
            "investor_types": ["venture capital"],
            "rounds_reached": ["Round A"],
            "founded_at": "2021-01-01",
            "first_funding_at": "2021-06-01",
            "last_funding_at": "2021-06-01",
            "consent": True,
        }
        res = client.post("/v1/evaluations", json=payload)
        assert res.status_code == 202
        eval_id = res.json()["evaluation_id"]

        # Fetch report
        rep_res = client.get(f"/v1/evaluations/{eval_id}/report")
        assert rep_res.status_code == 200
        rep_data = rep_res.json()

        # Fetch recommendations
        rec_res = client.get(f"/v1/evaluations/{eval_id}/recommendations")
        assert rec_res.status_code == 200
        rec_data = rec_res.json()

        return {
            "eval_id": eval_id,
            "index": index,
            "sections_count": len(rep_data["sections"]),
            "recs_count": len(rec_data["recommendations"]),
        }

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(_submit_single, i) for i in range(concurrent_requests)]
        results = [f.result() for f in as_completed(futures)]

    assert len(results) == concurrent_requests

    # Verify all evaluation IDs are distinct (no collision)
    eval_ids = {r["eval_id"] for r in results}
    assert len(eval_ids) == concurrent_requests

    # Verify all reports generated full 8 sections
    for r in results:
        assert r["sections_count"] == 8
        assert r["recs_count"] > 0
