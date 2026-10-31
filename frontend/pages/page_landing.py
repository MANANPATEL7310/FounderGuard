"""Landing page: consent + privacy notice + backend health check."""
import streamlit as st
from frontend import api_client


def render(goto):
    # Brand-led hero. All user journeys and backend calls below stay unchanged.
    # Preserve the app's established Streamlit title contract; the branded headline below is visible.
    st.title("Startup Evaluation", anchor="landing-page-title")
    st.markdown(
        """
        <section class="fg-hero">
            <div class="hero-badge">✦ Analytical intelligence platform</div>
            <h1 class="fg-hero-title">Move from instinct to <span>evidence.</span></h1>
            <p class="fg-hero-copy">
                FounderGuard gives your startup idea a clear, multi-model evaluation—so you can spot assumptions,
                understand risk signals, and focus your next move with confidence.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    stat_a, stat_b, stat_c = st.columns(3)
    with stat_a:
        st.markdown('<div class="fg-stat"><div class="fg-stat-value">4 models</div><div class="fg-stat-label">Independent perspectives</div></div>', unsafe_allow_html=True)
    with stat_b:
        st.markdown('<div class="fg-stat"><div class="fg-stat-value">Private</div><div class="fg-stat-label">In-memory processing</div></div>', unsafe_allow_html=True)
    with stat_c:
        st.markdown('<div class="fg-stat"><div class="fg-stat-value">Practical</div><div class="fg-stat-label">Clear next-step recommendations</div></div>', unsafe_allow_html=True)
    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

    # Backend health check
    if not api_client.check_backend_health():
        st.error(
            "Notice: The evaluation backend is not reachable. "
            "Start it with: `uvicorn backend.main:app --port 8000`"
        )
        if st.button("Retry Connection"):
            st.rerun()
        return

    # 4 Model Cards Grid
    st.markdown('<div class="fg-section-kicker">How it works</div>', unsafe_allow_html=True)
    st.markdown("### A balanced view, not one opaque score")
    st.caption("Each model evaluates your startup from a distinct statistical or qualitative perspective. Results are kept separate so you can see what each signal means.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            <div class="fg-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                    <span class="fg-card-title">Model A — Outcome Classifier</span>
                    <span class="model-badge">CatBoost GBDT</span>
                </div>
                <p class="fg-card-copy">
                    Predicts Operating vs. Closed status based on capital timeline, funding velocity, location, and industry cohort data.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="fg-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                    <span class="fg-card-title">Model C — Idea Evaluator</span>
                    <span class="model-badge">PyTorch BiGRU</span>
                </div>
                <p class="fg-card-copy">
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
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                    <span class="fg-card-title">Model B — Risk Estimator</span>
                    <span class="model-badge">Calibrated LogReg</span>
                </div>
                <p class="fg-card-copy">
                    Calculates a relative failure probability score among funded US startups, identifying top positive and negative financial levers.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="fg-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                    <span class="fg-card-title">Model D — Pattern Matcher</span>
                    <span class="model-badge">Multi-Label LSA</span>
                </div>
                <p class="fg-card-copy">
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
        <div class="fg-trust-card">
            <div style="font-weight:800;font-size:0.95rem;margin-bottom:4px;">
                🔒 Privacy &amp; transparency, built in
            </div>
            <p style="font-size:0.88rem;margin:0;line-height:1.5;">
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
        if st.button("Start Evaluation", disabled=not consent, type="primary", use_container_width=True):
            goto("form", step=1)
    with col_btn2:
        if st.button("About the Models", use_container_width=True):
            goto("about")
