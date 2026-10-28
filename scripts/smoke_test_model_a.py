#!/usr/bin/env python3
"""Smoke test and contract verification for Model A (Startup Outcome Classifier)."""
import sys
import pickle
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "models" / "model_a" / "v1"))
import startup_features as sf

def main():
    artifact_path = ROOT / "models" / "model_a" / "v1" / "startup_outcome_classifier.pkl"
    print(f"Loading Model A artifact from: {artifact_path}")
    
    with open(artifact_path, "rb") as f:
        bundle = pickle.load(f)
        
    print("\n================ MODEL METADATA ================")
    print(f"Bundle Type: {type(bundle)}")
    print(f"Bundle Keys: {list(bundle.keys())}")
    
    clf = bundle["model"]
    model_name = bundle.get("model_name", "CatBoost")
    print(f"Model Name: {model_name}")
    print(f"Classifier Class: {clf.__class__.__name__}")
    print(f"Class labels (classes_): {clf.classes_}")
    print(f"Feature names (feature_names_): {clf.feature_names_}")
    print(f"Raw input columns expected: {bundle.get('raw_columns')}")
        
    # Read one real record from dataset
    data_path = ROOT / "material" / "datasets" / "big_startup_secsees_dataset.csv"
    df = pd.read_csv(data_path)
    real_sample = df.iloc[0:1]
    print("\n================ TEST 0: REAL DATASET RECORD ================")
    print("Raw sample:")
    print(real_sample[['name', 'category_list', 'funding_total_usd', 'country_code', 'state_code', 'funding_rounds', 'founded_at']].to_dict(orient='records')[0])
    
    feats_0 = sf.engineer_features(real_sample)
    print("Engineered features:")
    print(feats_0.to_dict(orient='records')[0])
    
    pred_0 = clf.predict(feats_0)
    proba_0 = clf.predict_proba(feats_0)
    print(f"Native Prediction: {pred_0}")
    print(f"Native Probabilities: {proba_0}")
        
    print("\n================ TEST 1: COMPLETE FUNDED US STARTUP ================")
    rec_funded = pd.DataFrame([{
        "homepage_url": "https://exampleai.com",
        "category_list": "Software|Artificial Intelligence|Enterprise",
        "funding_total_usd": 5000000.0,
        "country_code": "USA",
        "state_code": "CA",
        "region": "SF Bay Area",
        "city": "San Francisco",
        "funding_rounds": 2,
        "founded_at": "2020-01-15",
        "first_funding_at": "2020-06-01",
        "last_funding_at": "2021-09-01"
    }])
    feats_1 = sf.engineer_features(rec_funded)
    print("Engineered features:")
    print(feats_1.to_dict(orient='records')[0])
    pred_1 = clf.predict(feats_1)
    proba_1 = clf.predict_proba(feats_1)
    print(f"Prediction: {pred_1}")
    print(f"Probabilities (0: Closed, 1: Operating/Success): {proba_1}")

    print("\n================ TEST 2: PRE-FUNDING IDEA (NO FUNDING, NO DATES) ================")
    rec_prefunding = pd.DataFrame([{
        "homepage_url": None,
        "category_list": "Biotechnology",
        "funding_total_usd": None,
        "country_code": "USA",
        "state_code": "MA",
        "region": "Boston",
        "city": "Boston",
        "funding_rounds": 0,
        "founded_at": None,
        "first_funding_at": None,
        "last_funding_at": None
    }])
    feats_2 = sf.engineer_features(rec_prefunding)
    print("Engineered features:")
    print(feats_2.to_dict(orient='records')[0])
    pred_2 = clf.predict(feats_2)
    proba_2 = clf.predict_proba(feats_2)
    print(f"Prediction: {pred_2}")
    print(f"Probabilities (0: Closed, 1: Operating/Success): {proba_2}")

    print("\n================ TEST 3: NON-US STARTUP ================")
    rec_non_us = pd.DataFrame([{
        "homepage_url": "https://example.co.uk",
        "category_list": "E-Commerce|FinTech",
        "funding_total_usd": 1200000.0,
        "country_code": "GBR",
        "state_code": None,
        "region": "London",
        "city": "London",
        "funding_rounds": 1,
        "founded_at": "2021-03-01",
        "first_funding_at": "2022-01-15",
        "last_funding_at": "2022-01-15"
    }])
    feats_3 = sf.engineer_features(rec_non_us)
    print("Engineered features:")
    print(feats_3.to_dict(orient='records')[0])
    pred_3 = clf.predict(feats_3)
    proba_3 = clf.predict_proba(feats_3)
    print(f"Prediction: {pred_3}")
    print(f"Probabilities (0: Closed, 1: Operating/Success): {proba_3}")

if __name__ == "__main__":
    main()
