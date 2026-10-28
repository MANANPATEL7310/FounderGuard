# Confirmed Model Contracts

This document specifies the verified input requirements, output schemas, and runtime contracts for all four models in the system. These contracts were confirmed by loading the trained artifacts in the isolated runtime environment and executing smoke tests against actual dataset records.

---

## 1. Summary of Model Artifacts & Environment

- **Python Runtime:** `3.11.15`
- **Pinned Library Versions:**
  - `scikit-learn`: `1.6.1`
  - `numpy`: `2.1.3`
  - `pandas`: `3.1.0`
  - `torch`: `2.14.1`
  - `joblib`: `1.6.0`
  - `catboost`: `1.2.10`
  - `scipy`: `1.17.1`

| Model | ID | Artifact Files | Format & Loader | Model Architecture / Type |
|---|---|---|---|---|
| **A** | `model_a` | `startup_outcome_classifier.pkl`, `startup_features.py` | `.pkl` via `pickle` | `CatBoostClassifier` (inside dictionary bundle) |
| **B** | `model_b` | `model_b_failure_risk.joblib`, `model_b_inference.py`, `model_b_metadata.json` | `.joblib` via `joblib` | `LogisticRegression` + Platt calibration (`CalibratedClassifierCV`) |
| **C** | `model_c` | `model_c_encoder.pt`, `model_c_inference.py`, `model_c_metadata.json` | `.pt` via `torch.load` | PyTorch BiGRU + Attention Pooling + Rule Engine |
| **D** | `model_d` | `model_d_classifier.joblib`, `cases.csv`, `case_embeddings.npy`, `label_config.json`, `model_d_inference.py`, `model_d_metadata.json` | `.joblib` + `.npy` + `.csv` via `joblib`/`numpy` | Multilabel Calibrated `LogisticRegression` with offline LSA encoder |

---

## 2. Model A Contract (Startup Outcome Classifier)

### 2.1 Artifact Structure & Model Type
- **Container:** Python dictionary with keys `['model', 'model_name', 'raw_columns', 'feature_columns']`.
- **Model Object:** `catboost.core.CatBoostClassifier` (Iterations: 600, Depth: 6, LR: 0.05, Auto Class Weights: Balanced).
- **Target Definition & Class Labels:**
  - `classes_`: `[0, 1]`
  - `0`: **Closed / Failure**
  - `1`: **Operating / Acquired / IPO (Active / Success)**

### 2.2 Expected Input Columns
`startup_features.py` defines `engineer_features(df)` requiring 11 raw columns:
1. `homepage_url` (*string, optional*)
2. `category_list` (*pipe-separated string, e.g. "Software|SaaS|Enterprise"*)
3. `funding_total_usd` (*numeric or formatted string, e.g. "5000000"*)
4. `country_code` (*3-letter ISO code, e.g. "USA", "GBR", "IND"*)
5. `state_code` (*2-letter US state or regional code*)
6. `region` (*string, e.g. "SF Bay Area"*)
7. `city` (*string, e.g. "San Francisco"*)
8. `funding_rounds` (*numeric integer*)
9. `founded_at` (*date string YYYY-MM-DD*)
10. `first_funding_at` (*date string YYYY-MM-DD*)
11. `last_funding_at` (*date string YYYY-MM-DD*)

### 2.3 Engineered Features (Exact Order of 17 Features)
- **12 Numeric Features:**
  1. `funding_rounds`
  2. `funding_total`
  3. `funding_total_log` (`log1p(funding_total)`)
  4. `funding_missing` (binary flag: 1 if funding missing, 0 otherwise)
  5. `funding_per_round` (`funding_total / funding_rounds`)
  6. `founded_year`
  7. `first_funding_year`
  8. `last_funding_year`
  9. `years_to_first_funding` (`(first_funding - founded) in years`)
  10. `funding_span_years` (`(last_funding - first_funding) in years`)
  11. `n_categories` (count of pipe-separated categories)
  12. `has_homepage` (1 if `homepage_url` present, 0 otherwise)
- **5 Categorical Features:**
  13. `country_code`
  14. `state_code` (imputed to `'missing'` if None)
  15. `region` (imputed to `'missing'` if None)
  16. `city` (imputed to `'missing'` if None)
  17. `primary_category` (first token in `category_list`, or `'missing'`)

### 2.4 Empirical Behavior on Three Test Scenarios
1. **Complete Funded US Startup:**
   - Raw Input: \$5.0M funding, 2 rounds, CA / SF Bay Area, 2020 founding.
   - Prediction: `1` (Operating / Success)
   - Probabilities: `P(Closed)=16.6%`, `P(Operating/Success)=83.4%`.
2. **Pre-funding Idea (No funding, no dates):**
   - Raw Input: `funding_total_usd=None`, `funding_rounds=0`, dates=None.
   - Prediction: `0` (Closed / Failure)
   - Probabilities: `P(Closed)=52.2%`, `P(Operating/Success)=47.8%`.
   - *Observation:* Model A does not crash on missing values because CatBoost handles NaNs and `funding_missing=1.0` is an explicit feature. However, missing traction leans the outcome toward Closed.
3. **Non-US Startup:**
   - Raw Input: London, GBR, `state_code=None`.
   - Prediction: `1` (Operating / Success)
   - Probabilities: `P(Closed)=36.4%`, `P(Operating/Success)=63.6%`.
   - *Observation:* Non-US records are handled gracefully (`state_code` defaults to `'missing'`).

---

## 3. Model B Contract (Failure Risk Classifier)

### 3.1 Model Architecture & Purpose
- **Architecture:** `LogisticRegression` with Platt sigmoid calibration (`CalibratedClassifierCV`).
- **Meaning:** Predicts relative probability of being closed rather than acquired among **funded US startups**.

### 3.2 Expected Input
Requires a dictionary or DataFrame row with 10 fields:
- `category_code`: *string* (e.g. `'software'`, `'biotech'`)
- `state_code`: *string* (e.g. `'CA'`, `'NY'`; grouped to CA, NY, MA, TX or OTHER)
- `funding_total_usd`: *float > 0*
- `funding_rounds`: *int >= 1*
- `has_VC`: *int/bool (0 or 1)*
- `has_angel`: *int/bool (0 or 1)*
- `has_roundA`: *int/bool (0 or 1)*
- `has_roundB`: *int/bool (0 or 1)*
- `has_roundC`: *int/bool (0 or 1)*
- `has_roundD`: *int/bool (0 or 1)*

*Applicability Constraint:* Only applicable for funded startups (`funding_total_usd > 0` and `funding_rounds >= 1`). Pre-funding ideas must be marked **not applicable**.

### 3.3 Output Keys
```python
{
    "failure_probability": float,       # e.g. 0.6801
    "risk_score": float,                # 100 x failure_probability, e.g. 68.0
    "risk_level": str,                  # "Low" (<25), "Moderate" (25-50), "High" (50-75), "Very High" (>=75)
    "meaning": str,                     # Explanatory text from metadata
    "top_contributing_features": list,  # [{feature, value, effect_on_probability, direction}, ...]
    "model": str,                       # "LogisticRegression + Platt calibration"
    "test_metrics": dict,               # ROC-AUC (0.7232), Brier (0.2066), etc.
    "warnings": list                    # Warnings regarding unseen category, non-US state, or funding range
}
```

---

## 4. Model C Contract (Idea Text Encoder & Aspect Extractor)

### 4.1 Model Architecture & Purpose
- **Architecture:** PyTorch BiGRU with additive attention pooling and projection layer, trained on 10 sector classes + rule-based aspect extraction engine.
- **Purpose:** Checks consistency of idea pitch against declared sector and evaluates text completeness across key business dimensions. **Produces NO predictive failure/success score.**

### 4.2 Expected Input
- `idea_text`: *string* (free-text idea pitch)
- `declared_sector`: *string, optional* (e.g. `"SaaS"`, `"Consumer"`, `"FinTech"`, `"AI"`)
- `extra`: *dict, optional* (containing optional detailed keys: `problem`, `target_customer`, `business_model`, `validation_evidence`, `competitors`, `traction`)

### 4.3 Output Keys
```python
{
    "provided_fields": list,            # List of extra fields provided
    "sector_check": {
        "declared_sector": str or None,
        "predicted_top_sectors": list,  # [{"sector": str, "probability": float}, ...]
        "consistent": bool or None,     # True, False, or None
        "note": str
    },
    "nn_confidence": float,
    "key_terms_attended_by_nn": list,   # Top tokens attended by attention layer
    "aspect_findings": list,            # 8 aspects: status ("evidence_found", "not_stated", "partial", "risk_signals_found")
    "strengths": list,                  # Aspects with clear evidence found
    "potential_weaknesses_and_gaps": list,
    "missing_information_questions": list,
    "vague_terms": list,                # Detected buzzwords (e.g. "ai-driven", "streamline")
    "similar_startups": list,           # Nearest training corpus pitches with cosine similarity
    "similarity_note": str,
    "warnings": list,
    "validation_status": dict,
    "limitations": list
}
```

---

## 5. Model D Contract (Multilabel Failure Category Classifier)

### 5.1 Model Architecture & Purpose
- **Architecture:** Calibrated multilabel `LogisticRegression` estimators per category with an offline LSA encoder (TF-IDF 1-2gram + TruncatedSVD 256-dim).
- **Purpose:** Detects presence of 8 historical failure themes in the startup narrative.

### 5.2 Expected Input
- `text`: *string* (startup description, plan, and challenges)
- `top_k_cases`: *int* (default 3, number of similar historical post-mortems per category)

### 5.3 Modelled Categories (8 Total)
1. `market_demand` ("No market need")
2. `funding_cashflow` ("Funding and cash-flow problems")
3. `competition_differentiation` ("Outcompeted or lack of differentiation")
4. `unit_economics_pricing` ("Poor unit economics or pricing")
5. `acquisition_retention` ("Customer acquisition and retention difficulties")
6. `team_operations` ("Team, co-founder, or operational issues")
7. `weak_business_model` ("Flawed or unviable business model")
8. `product_market_fit` ("Failure to achieve product-market fit")

### 5.4 Output Keys
```python
{
    "model": "D",
    "categories": [
        {
            "category": str,                    # e.g. "unit_economics_pricing"
            "label": str,                       # e.g. "Poor unit economics or pricing"
            "supported": bool,
            "probability": float,               # Calibrated probability
            "threshold": float,                 # Decision threshold
            "predicted": bool,                  # True if probability >= threshold
            "label_quality": str,
            "evidence_sentence": str,           # Most representative sentence from input
            "keyword_matches": list,            # Matched rule keywords
            "similar_historical_failures": list # Historical cases with similarity and failure reason
        }, ...
    ],
    "predicted_categories": list,               # List of category IDs where predicted is True
    "ood": {
        "flagged": bool,                        # True if nearest case sim < threshold
        "nearest_case_similarity": float,
        "threshold": float
    },
    "warnings": list,
    "note": str,
    "meaning": str
}
```
