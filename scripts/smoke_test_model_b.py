#!/usr/bin/env python3
"""Smoke test for Model B (Failure Risk Classifier)."""
import sys
from pathlib import Path
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "models" / "model_b" / "v1"))
import model_b_inference as mb

def main():
    artifact_path = ROOT / "models" / "model_b" / "v1" / "model_b_failure_risk.joblib"
    print(f"Loading Model B artifact from: {artifact_path}")
    bundle = joblib.load(artifact_path)
    
    # Read one real record from material/datasets/startup data.csv
    data_path = ROOT / "material" / "datasets" / "startup data.csv"
    df = pd.read_csv(data_path)
    
    # Pick the first valid row with positive funding and at least 1 round
    sample = df[(df["funding_total_usd"] > 0) & (df["funding_rounds"] >= 1)].iloc[0]
    rec = {
        "category_code": sample["category_code"],
        "state_code": sample["state_code"],
        "funding_total_usd": sample["funding_total_usd"],
        "funding_rounds": sample["funding_rounds"],
        "has_VC": sample["has_VC"],
        "has_angel": sample["has_angel"],
        "has_roundA": sample["has_roundA"],
        "has_roundB": sample["has_roundB"],
        "has_roundC": sample["has_roundC"],
        "has_roundD": sample["has_roundD"]
    }
    
    print("\n--- Input Record ---")
    print(rec)
    
    out = mb.predict_failure_risk(bundle, rec)
    print("\n--- Native Output ---")
    import pprint
    pprint.pprint(out)
    return out

if __name__ == "__main__":
    main()
