#!/usr/bin/env python3
"""Smoke test for Model D (Failure Category Classifier)."""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "models" / "model_d" / "v1"))
import model_d_inference as md

def main():
    artifact_dir = ROOT / "models" / "model_d" / "v1"
    print(f"Loading Model D classifier from: {artifact_dir}")
    clf = md.FailureCategoryClassifier(str(artifact_dir))
    
    # Read one real record from startup-failures.csv
    data_path = ROOT / "material" / "datasets" / "startup-failures.csv"
    df = pd.read_csv(data_path)
    sample = df.iloc[0]
    
    text = f"{sample['name']}: {sample['failure_reason']}. {sample['lesson']}"
    print(f"\n--- Input Text ---")
    print(text)
    
    out = clf.predict(text)
    print("\n--- Native Output ---")
    import pprint
    pprint.pprint(out)
    return out

if __name__ == "__main__":
    main()
