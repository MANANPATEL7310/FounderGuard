"""About-the-models page: details on all four machine learning models."""
from __future__ import annotations
import streamlit as st
import requests
from frontend.config import BACKEND_URL


def render(goto):
    st.title("ℹ About the Machine Learning Models")
    st.caption("Architecture, training provenance, validation metrics, and limitations.")

    if st.button("← Back to Previous Screen"):
        goto("landing")

    # Fetch models catalog from backend
    try:
        r = requests.get(f"{BACKEND_URL}/v1/models", timeout=5)
        catalog = r.json() if r.status_code == 200 else {}
    except Exception:
        catalog = {}

    st.markdown("---")

    models_info = [
        {
            "id": "model_a",
            "name": "Model A — Startup Outcome Classifier",
            "arch": "CatBoost Classifier (Gradient Boosted Decision Trees)",
            "trained_on": "big_startup_secsees_dataset (Crunchbase historical acquisitions & closures)",
            "runtime": "CatBoost / scikit-learn / pandas",
            "target": "Binary: 0 = Closed / Failed, 1 = Operating / Acquired / IPO",
            "caveat": "Requires founding and funding milestone dates. Predictions on recent cohorts (>2015) may experience temporal distribution drift due to right-censoring.",
        },
        {
            "id": "model_b",
            "name": "Model B — Failure Risk Estimator",
            "arch": "Logistic Regression with Platt Sigmoid Calibration (CalibratedClassifierCV)",
            "trained_on": "923 US startups (closed vs acquired)",
            "runtime": "scikit-learn / joblib",
            "target": "Calibrated relative probability of being closed rather than acquired among funded US startups.",
            "caveat": "US-only dataset. Applicable only to funded startups (funding > $0 and rounds >= 1). Does NOT predict failure probability in N years; it is a relative risk score compared to historical cohorts.",
        },
        {
            "id": "model_c",
            "name": "Model C — Idea Evaluator & Aspect Extractor",
            "arch": "PyTorch BiGRU with Additive Attention Pooling + Heuristic Rule Engine",
            "trained_on": "10,000 short startup pitches across 10 industry sectors",
            "runtime": "PyTorch (CPU)",
            "target": "Sector consistency check and extraction of 8 key business aspects (customer, problem, traction, etc.).",
            "caveat": "Produces NO numeric predictive score. Aspect findings are unvalidated heuristic rules. Blank fields are treated as 'not stated', never as negative evidence.",
        },
        {
            "id": "model_d",
            "name": "Model D — Multilabel Failure Category Classifier",
            "arch": "Calibrated Multilabel Logistic Regression with Offline LSA Encoder (TF-IDF + TruncatedSVD)",
            "trained_on": "startup-failures.csv post-mortems with rule-derived labels",
            "runtime": "scikit-learn / numpy / joblib",
            "target": "8 historical failure themes (e.g. no market need, unit economics, cash-flow problems).",
            "caveat": "Probabilities indicate resemblance to past post-mortem narratives, not confirmed future causes. When text similarity is below threshold, the Out-of-Distribution flag is raised.",
        },
    ]

    for m in models_info:
        st.markdown(f"### {m['name']}")
        st.markdown(f"- **Architecture:** {m['arch']}")
        st.markdown(f"- **Trained On:** {m['trained_on']}")
        st.markdown(f"- **Runtime Libraries:** `{m['runtime']}`")
        st.markdown(f"- **Target / Objective:** {m['target']}")
        st.markdown(f"- **Key Caveat & Limitation:** {m['caveat']}")

        # Show manifest details if available
        if catalog and m["id"] in catalog:
            with st.expander(f"View Technical Manifest ({m['id']})"):
                st.json(catalog[m["id"]], expanded=False)

        st.markdown("---")

