"""Landing page: consent + privacy notice + backend health check."""
import streamlit as st
from frontend import api_client


def render(goto):
    # Header badge & Title
    st.markdown('<div class="hero-badge">🛡 Multi-Model AI Advisory Platform</div>', unsafe_allow_html=True)
    st.title("🚀 Startup Evaluation — FounderGuard AI")
    st.markdown(
        '<p style="font-size:1.1rem;color:#94A3B8;margin-bottom:24px;max-width:750px;">'
        'A multi-model machine learning pipeline for startup risk analysis, '
        'failure pattern classification, and grounded strategic recommendations.'
        '</p>',
        unsafe_allow_html=True,
    )

    # Backend health check
    if not api_client.check_backend_health():
        st.error(
            "⚠ The evaluation backend is not reachable. "
            "Start it with: `uvicorn backend.main:app --port 8000`"
        )
        if st.button("🔄 Retry connection"):
            st.rerun()
        return

    # 4 Model Cards Grid
    st.markdown("### 🤖 Independent Analytical Models")
    st.caption("Each model evaluates your startup from a distinct statistical or qualitative perspective. Models are never blended into a single combined score.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            <div class="fg-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-size:1.1rem;font-weight:700;color:#F8FAFC;">Model A — Outcome Classifier</span>
                    <span style="background:rgba(99,102,241,0.2);color:#A5B4FC;padding:2px 8px;border-radius:6px;font-size:0.75rem;font-weight:600;">CatBoost</span>
                </div>
                <p style="font-size:0.9rem;color:#94A3B8;margin:0;">
                    Predicts Operating vs. Closed status based on capital timeline, funding velocity, location, and industry cohort data.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="fg-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-size:1.1rem;font-weight:700;color:#F8FAFC;">Model C — Qualitative Idea Evaluator</span>
                    <span style="background:rgba(16,185,129,0.2);color:#6EE7B7;padding:2px 8px;border-radius:6px;font-size:0.75rem;font-weight:600;">PyTorch BiGRU</span>
                </div>
                <p style="font-size:0.9rem;color:#94A3B8;margin:0;">
                    Evaluates narrative strength across 8 core business dimensions, detecting qualitative risks, vague buzzwords, and missing details.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="fg-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-size:1.1rem;font-weight:700;color:#F8FAFC;">Model B — Calibrated Risk Estimator</span>
                    <span style="background:rgba(245,158,11,0.2);color:#FCD34D;padding:2px 8px;border-radius:6px;font-size:0.75rem;font-weight:600;">Platt Calibrated</span>
                </div>
                <p style="font-size:0.9rem;color:#94A3B8;margin:0;">
                    Calculates a relative failure probability score among funded US startups, identifying top positive and negative financial levers.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="fg-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <span style="font-size:1.1rem;font-weight:700;color:#F8FAFC;">Model D — Failure Category Matcher</span>
                    <span style="background:rgba(239,68,68,0.2);color:#FCA5A5;padding:2px 8px;border-radius:6px;font-size:0.75rem;font-weight:600;">LSA Multi-Label</span>
                </div>
                <p style="font-size:0.9rem;color:#94A3B8;margin:0;">
                    Matches pitch narratives against 1,000+ historical post-mortems to detect failure modes (e.g. burn rate, unit economics friction).
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Privacy & Consent Section
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="background:rgba(30,41,59,0.5);border:1px solid rgba(148,163,184,0.15);border-radius:10px;padding:16px 20px;margin-bottom:20px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <span style="font-size:1.1rem;">🔒</span>
                <span style="font-weight:700;color:#F1F5F9;font-size:0.95rem;">Privacy & Transparency Guarantee</span>
            </div>
            <p style="font-size:0.88rem;color:#94A3B8;margin:0;">
                Your submission is processed strictly in-memory to generate the report. We do not sell data or train models on user inputs. 
                You can permanently purge all evaluation records and lineage at any time using the <b>Delete My Data</b> button.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    consent = st.checkbox(
        "I understand this is a statistical analysis tool, not investment advice. "
        "Results reflect historical patterns and do not guarantee success or failure. "
        "I consent to my inputs being processed to generate an evaluation.",
        key="landing_consent",
    )

    col_btn1, col_btn2 = st.columns([2, 5])
    with col_btn1:
        if st.button("🚀 Start Evaluation →", disabled=not consent, type="primary", use_container_width=True):
            goto("form", step=1)
    with col_btn2:
        if st.button("ℹ About the Models", use_container_width=True):
            goto("about")
