#!/usr/bin/env python3
"""Smoke test for Model C (Idea Text Encoder & Aspect Extractor)."""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "models" / "model_c" / "v1"))
import model_c_inference as mc

def main():
    artifact_path = ROOT / "models" / "model_c" / "v1" / "model_c_encoder.pt"
    print(f"Loading Model C artifact from: {artifact_path}")
    bundle = mc.load_bundle(str(artifact_path))
    
    # Read one real record from dataset
    data_path = ROOT / "material" / "datasets" / "venturematch_startups_10k_enriched_ckpt%20.csv"
    df = pd.read_csv(data_path)
    sample = df.iloc[0]
    
    pitch = sample["pitch"]
    declared_sector = sample["sector"]
    extra = {
        "problem": "Manual supply chain friction and slow operations",
        "target_customer": "Warehouses, suppliers and retailers",
        "business_model": sample.get("business_model", "Enterprise SaaS")
    }
    
    print("\n--- Input Idea ---")
    print(f"Pitch: {pitch}")
    print(f"Declared Sector: {declared_sector}")
    print(f"Extra: {extra}")
    
    out = mc.evaluate_idea(bundle, pitch, declared_sector=declared_sector, extra=extra)
    print("\n--- Native Output ---")
    import pprint
    pprint.pprint(out)
    return out

if __name__ == "__main__":
    main()
