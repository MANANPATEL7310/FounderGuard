"""Automated tests verifying that all 4 models load and run in the environment."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import joblib
import pickle

ROOT = Path(__file__).resolve().parent.parent

def test_model_a_loads_and_predicts():
    sys.path.insert(0, str(ROOT / "models" / "model_a" / "v1"))
    import startup_features as sf
    artifact = ROOT / "models" / "model_a" / "v1" / "startup_outcome_classifier.pkl"
    assert artifact.exists(), "Model A artifact missing"
    
    with open(artifact, "rb") as f:
        bundle = pickle.load(f)
    assert "model" in bundle
    clf = bundle["model"]
    
    # Test record
    rec = pd.DataFrame([{
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
    }])
    feats = sf.engineer_features(rec)
    preds = clf.predict(feats)
    probas = clf.predict_proba(feats)
    assert len(preds) == 1
    assert probas.shape == (1, 2)

def test_model_b_loads_and_predicts():
    sys.path.insert(0, str(ROOT / "models" / "model_b" / "v1"))
    import model_b_inference as mb
    artifact = ROOT / "models" / "model_b" / "v1" / "model_b_failure_risk.joblib"
    assert artifact.exists(), "Model B artifact missing"
    
    bundle = joblib.load(artifact)
    rec = {
        "category_code": "software",
        "state_code": "CA",
        "funding_total_usd": 1500000.0,
        "funding_rounds": 2,
        "has_VC": 1,
        "has_angel": 1,
        "has_roundA": 1,
        "has_roundB": 0,
        "has_roundC": 0,
        "has_roundD": 0
    }
    res = mb.predict_failure_risk(bundle, rec)
    assert "risk_score" in res
    assert 0 <= res["risk_score"] <= 100
    assert res["risk_level"] in ["Low", "Moderate", "High", "Very High"]

def test_model_c_loads_and_predicts():
    sys.path.insert(0, str(ROOT / "models" / "model_c" / "v1"))
    import model_c_inference as mc
    artifact = ROOT / "models" / "model_c" / "v1" / "model_c_encoder.pt"
    assert artifact.exists(), "Model C artifact missing"
    
    bundle = mc.load_bundle(str(artifact))
    pitch = "AI-powered inventory and supply chain optimization software for warehouse operators."
    res = mc.evaluate_idea(bundle, pitch, declared_sector="SaaS")
    assert "sector_check" in res
    assert "aspect_findings" in res
    assert len(res["aspect_findings"]) == 8

def test_model_d_loads_and_predicts():
    sys.path.insert(0, str(ROOT / "models" / "model_d" / "v1"))
    import model_d_inference as md
    artifact_dir = ROOT / "models" / "model_d" / "v1"
    assert (artifact_dir / "model_d_classifier.joblib").exists(), "Model D classifier missing"
    
    clf = md.FailureCategoryClassifier(str(artifact_dir))
    text = "We built a food delivery app with high customer acquisition costs and low unit margins, running out of cash."
    res = clf.predict(text)
    assert "categories" in res
    assert len(res["categories"]) == 8
    assert "predicted_categories" in res
