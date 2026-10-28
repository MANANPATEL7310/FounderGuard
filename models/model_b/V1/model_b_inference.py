
import numpy as np
import pandas as pd

RISK_BINS   = [0, 25, 50, 75, 100.0001]
RISK_LABELS = ["Low", "Moderate", "High", "Very High"]

REQUIRED_FIELDS = ["category_code", "state_code", "funding_total_usd", "funding_rounds",
                   "has_VC", "has_angel", "has_roundA", "has_roundB", "has_roundC", "has_roundD"]

def _to_logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p)).reshape(-1, 1)

def engineer(d):
    out = pd.DataFrame(index=d.index)
    out["category_code"] = d["category_code"].astype(str).str.lower()
    st = d["state_code"].astype(str).str.upper()
    out["state_group"] = st.where(st.isin(["CA", "NY", "MA", "TX"]), "OTHER")
    out["log_funding_total"] = np.log10(d["funding_total_usd"].clip(lower=1))
    out["funding_rounds"] = d["funding_rounds"]
    out["funding_per_round"] = np.log10((d["funding_total_usd"] / d["funding_rounds"].clip(lower=1)).clip(lower=1))
    for c in ["has_VC", "has_angel", "has_roundA", "has_roundB", "has_roundC", "has_roundD"]:
        out[c] = d[c].astype(int)
    out["n_investor_types"] = out["has_VC"] + out["has_angel"]
    out["highest_round"] = np.select([d["has_roundD"] == 1, d["has_roundC"] == 1,
                                      d["has_roundB"] == 1, d["has_roundA"] == 1], [4, 3, 2, 1], default=0)
    return out

def validate_input(rec):
    # Validate/normalise one startup record (dict). Returns (clean_dict, warnings).
    warnings, clean = [], dict(rec)
    missing = [k for k in REQUIRED_FIELDS if clean.get(k) is None]
    if missing:
        raise ValueError(f"Model B needs these fields: {missing}")
    clean["funding_total_usd"] = float(clean["funding_total_usd"])
    clean["funding_rounds"] = int(clean["funding_rounds"])
    if clean["funding_total_usd"] <= 0 or clean["funding_rounds"] < 1:
        raise ValueError("Model B was trained on funded startups: funding_total_usd > 0 and funding_rounds >= 1 required.")
    for k in ["has_VC", "has_angel", "has_roundA", "has_roundB", "has_roundC", "has_roundD"]:
        clean[k] = int(bool(clean[k]))
    return clean, warnings

def _predict_raw(bundle, X):
    p_raw = bundle["model"].predict_proba(X)[:, 1]
    return bundle["calibrator"].predict_proba(_to_logit(p_raw))[:, 1]

def predict_failure_risk(bundle, rec, top_k=4):
    clean, warnings = validate_input(rec)
    meta = bundle["metadata"]
    if clean["category_code"].lower() not in meta["known_categories"]:
        warnings.append(f"Category '{clean['category_code']}' was rare/unseen in training; it is treated as 'other/infrequent'.")
    if clean["state_code"].upper() not in meta["known_states"]:
        warnings.append("State/region not seen in training data (US-only data); location effect is treated as 'OTHER'.")
    lo, hi = meta["train_funding_range_usd"]
    if not (lo <= clean["funding_total_usd"] <= hi):
        warnings.append("Funding amount is outside the range seen in training; extrapolation is unreliable.")
    X = engineer(pd.DataFrame([clean]))
    p = float(_predict_raw(bundle, X)[0])
    score = 100 * p
    level = pd.cut([score], bins=RISK_BINS, labels=RISK_LABELS, right=False)[0]

    # local explanation by feature ablation (replace a feature by its training reference value)
    ref = pd.Series(meta["reference_values"])
    contribs = []
    for f in X.columns:
        Xa = X.copy(); Xa[f] = ref[f] if f in ref else Xa[f]
        if f in meta["numeric_features"]:
            Xa[f] = float(ref[f])
        contribs.append((f, X[f].iloc[0], p - float(_predict_raw(bundle, Xa)[0])))
    contribs.sort(key=lambda t: abs(t[2]), reverse=True)
    factors = [{"feature": f, "value": (v if isinstance(v, str) else float(v)),
                "effect_on_probability": round(d, 4),
                "direction": "raises risk" if d > 0 else "lowers risk"} for f, v, d in contribs[:top_k]]
    return {
        "failure_probability": round(p, 4),
        "risk_score": round(score, 1),
        "risk_level": str(level),
        "meaning": meta["score_meaning"],
        "top_contributing_features": factors,
        "model": meta["model_name"],
        "test_metrics": meta["test_metrics"],
        "warnings": warnings,
    }
