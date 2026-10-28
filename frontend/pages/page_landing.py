"""Landing page: consent + privacy notice + backend health check."""
import streamlit as st
from frontend import api_client


def render(goto):
    st.title("🚀 Startup Evaluation")
    st.caption("Multi-model machine learning pipeline for startup analysis")

    # Backend health
    if not api_client.check_backend_health():
        st.error(
            "⚠ The evaluation backend is not reachable. "
            "Start it with: `uvicorn backend.main:app --port 8000`"
        )
        if st.button("🔄 Retry connection"):
            st.rerun()
        return

    st.success("✓ Backend is online and ready.")

    st.markdown("---")
    st.markdown(
        """
        This tool runs your startup idea through four independent trained machine-learning models:

        | Model | What it does |
        |---|---|
        | **A — Outcome Classifier** | Predicts operating vs closed based on funding history (CatBoost) |
        | **B — Risk Estimator** | Calibrated relative failure probability among funded US startups |
        | **C — Idea Evaluator** | NLP analysis of your pitch across 8 business dimensions |
        | **D — Failure Categories** | Detects historical failure themes in your narrative text |

        Models are shown **separately** — their outputs mean different things and are never combined into one score.

        > **Privacy:** Your idea text is processed only to generate this evaluation.
        > Nothing is stored permanently. Use the **Delete my data** button on the report page
        > to remove your submission at any time.
        """
    )

    st.markdown("---")
    consent = st.checkbox(
        "I understand this is a statistical analysis tool, not investment advice. "
        "Results reflect historical patterns and do not guarantee success or failure. "
        "I consent to my inputs being processed to generate an evaluation.",
        key="landing_consent",
    )

    col1, col2 = st.columns([2, 6])
    with col1:
        if st.button("Start Evaluation →", disabled=not consent, type="primary", use_container_width=True):
            goto("form", step=1)
    with col2:
        if st.button("About the Models", use_container_width=True):
            goto("about")

