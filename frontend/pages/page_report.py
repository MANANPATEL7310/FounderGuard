"""Report Page: renders the full 8-section multi-model evaluation."""
from __future__ import annotations
import streamlit as st
from frontend import api_client
from frontend.ui_helpers import (
    ASPECT_ICONS,
    INTERP_ICONS,
    RISK_COLORS,
    error_card,
    not_applicable_card,
    ood_banner,
    year_warning_banner,
)


def render(goto, start_over):
    report = st.session_state.get("report")
    eval_id = st.session_state.get("eval_id")

    # If no report loaded, try to fetch it
    if not report and eval_id:
        report = api_client.get_report(eval_id)
        if report:
            st.session_state["report"] = report

    if not report:
        st.error("No report available to display.")
        if st.button("← Return to Start"):
            start_over()
        return

    meta = report.get("meta", {})
    input_sum = report.get("input_summary", {})
    models = report.get("models", {})
    interpretation = report.get("interpretation", {})
    trust = report.get("trust", {})
    key_factors = report.get("key_factors", {})
    sections = {s["section_number"]: s for s in report.get("sections", [])}

    # ── Sidebar Controls ──────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Evaluation Actions")
        st.write(f"**ID:** `{meta.get('evaluation_id', eval_id)}`")
        st.write(f"**Completed:** {meta.get('completed_at', '—')[:19].replace('T', ' ')}")
        st.markdown("---")

        if st.button("➕ Start New Evaluation", use_container_width=True):
            start_over()

        if st.button("ℹ About the Models", use_container_width=True):
            goto("about")

        st.markdown("---")
        st.markdown("#### Privacy & Data")
        if st.button("🗑 Delete My Data", type="secondary", use_container_width=True):
            if eval_id:
                api_client.delete_evaluation(eval_id)
            st.success("Your evaluation data has been deleted.")
            start_over()

    # ── Header ──────────────────────────────────────────────────────────────────
    pitch = input_sum.get("idea_description", "")
    title = pitch.split("\n")[0][:100] if pitch else "Startup Pitch Evaluation"
    st.title(f"📊 {title}")
    st.caption(
        f"Stage: **{input_sum.get('stage', '—')}** | "
        f"Industry: **{input_sum.get('industry', '—')}** | "
        f"Location: **{input_sum.get('country', '—')} {input_sum.get('state') or ''}** | "
        f"Report ID: `{meta.get('evaluation_id', eval_id)}`"
    )

    # ── Overall Interpretation Banner ───────────────────────────────────────────
    cat = interpretation.get("category", "Mixed picture")
    icon, bg_color = INTERP_ICONS.get(cat, ("⚪", "#f5f5f5"))
    st.markdown(
        f"""
        <div style="background-color:{bg_color};border-left:6px solid #455A64;padding:16px 20px;border-radius:6px;margin:12px 0 20px 0;">
            <div style="font-size:1.25rem;font-weight:700;margin-bottom:6px;">{icon} Overall Synthesis: {cat}</div>
            <div style="font-size:0.95rem;color:#333;margin-bottom:8px;">{interpretation.get('summary', '')}</div>
            <ul style="margin:0;padding-left:20px;font-size:0.88rem;color:#555;">
                {''.join(f'<li>{r}</li>' for r in interpretation.get('reasons', []))}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Tab navigation for the sections
    tab_report, tab_recs, tab_trust = st.tabs(["📑 Full 8-Section Report", "💡 Recommendations", "🛡 Trust & Limitations"])

    # ═════════════════════════════════════════════════════════════════════════════
    # TAB 1: 8-SECTION REPORT
    # ═════════════════════════════════════════════════════════════════════════════
    with tab_report:
        # SECTION 1: Executive Summary
        st.markdown("### Section 1: Executive Summary")
        sec1 = sections.get(1, {})
        sec1_content = sec1.get("content", {})
        st.info(sec1_content.get("summary_text", ""))

        st.markdown("---")

        # SECTION 2: Model A (Outcome Classifier)
        st.markdown("### Section 2: Predicted Outcome and Probabilities (Model A)")
        env_a = models.get("model_a", {})
        if not env_a:
            st.markdown(not_applicable_card("Model A", "No outcome data returned."), unsafe_allow_html=True)
        elif env_a.get("status") == "not_applicable":
            st.markdown(not_applicable_card("Model A", env_a.get("applicability_reason", "Pre-funding idea or missing required dates.")), unsafe_allow_html=True)
        elif env_a.get("status") == "error":
            st.markdown(error_card("Model A", env_a.get("applicability_reason", "Error during execution.")), unsafe_allow_html=True)
        else:
            data_a = env_a.get("data", {})
            for w in env_a.get("warnings", []):
                st.markdown(year_warning_banner(w), unsafe_allow_html=True)

            col_a1, col_a2 = st.columns([1, 1])
            with col_a1:
                outcome = data_a.get("predicted_outcome", "—")
                conf = data_a.get("confidence", 0.0)
                st.metric("Predicted Outcome", outcome, f"{conf*100:.1f}% confidence")
                st.caption(f"**Target Definition:** {data_a.get('target_definition', '')}")

                probs = data_a.get("probabilities", {})
                st.markdown("**Outcome Probabilities:**")
                st.write(f"• Closed / Failed: `{probs.get('closed', 0.0)*100:.1f}%`")
                st.progress(float(probs.get("closed", 0.0)))
                st.write(f"• Operating / Acquired / IPO: `{probs.get('operating_acquired_ipo', 0.0)*100:.1f}%`")
                st.progress(float(probs.get("operating_acquired_ipo", 0.0)))

            with col_a2:
                st.markdown("**Top Contributing Features:**")
                factors_a = data_a.get("top_contributing_features", [])
                if factors_a:
                    for f in factors_a:
                        st.markdown(f"- **{f.get('feature')}**: `{f.get('value')}` *(importance: {f.get('importance')})*")
                else:
                    st.caption("No individual factor scores available.")

        st.markdown("---")

        # SECTION 3: Model B (Failure Risk Estimator)
        st.markdown("### Section 3: Failure Probability and Risk Score (Model B)")
        env_b = models.get("model_b", {})
        if not env_b:
            st.markdown(not_applicable_card("Model B", "No risk data returned."), unsafe_allow_html=True)
        elif env_b.get("status") == "not_applicable":
            st.markdown(not_applicable_card("Model B", env_b.get("applicability_reason", "Trained on funded startups.")), unsafe_allow_html=True)
        elif env_b.get("status") == "error":
            st.markdown(error_card("Model B", env_b.get("applicability_reason", "Error during execution.")), unsafe_allow_html=True)
        else:
            data_b = env_b.get("data", {})
            for w in env_b.get("warnings", []):
                st.warning(f"⚠ {w}")

            score = data_b.get("risk_score", 0.0)
            level = data_b.get("risk_level", "Unknown")
            lvl_color = RISK_COLORS.get(level, "#757575")

            col_b1, col_b2 = st.columns([1, 1])
            with col_b1:
                st.markdown(
                    f"""
                    <div style="border:2px solid {lvl_color};border-radius:8px;padding:16px;text-align:center;">
                        <span style="font-size:0.9rem;text-transform:uppercase;color:#666;">Relative Failure Risk Score</span>
                        <div style="font-size:3rem;font-weight:800;color:{lvl_color};">{score:.1f} <span style="font-size:1.5rem;">/ 100</span></div>
                        <div style="display:inline-block;background:{lvl_color};color:white;padding:4px 12px;border-radius:12px;font-weight:600;font-size:0.9rem;">{level} Risk</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption(f"**Meaning:** {data_b.get('meaning', 'Relative risk among funded US startups.')}")

            with col_b2:
                st.markdown("**Top Contributing Factors:**")
                factors_b = data_b.get("top_contributing_features", [])
                if factors_b:
                    for f in factors_b:
                        direction = f.get("direction", "")
                        eff = f.get("effect_on_probability", 0.0)
                        sign = "+" if eff > 0 else ""
                        st.markdown(f"- **{f.get('feature')}**: `{f.get('value')}` → *{direction} risk ({sign}{eff*100:.1f}%)*")
                else:
                    st.caption("No individual factor scores available.")

        st.markdown("---")

        # SECTION 4: Model C (NLP Idea Evaluation & Aspect Findings)
        st.markdown("### Section 4: Idea Evaluation, Strengths & Missing Evidence (Model C)")
        env_c = models.get("model_c", {})
        if not env_c or env_c.get("status") != "ok":
            st.markdown(not_applicable_card("Model C", env_c.get("applicability_reason", "No evaluation data.")), unsafe_allow_html=True)
        else:
            data_c = env_c.get("data", {})
            for w in env_c.get("warnings", []):
                st.warning(f"⚠ {w}")

            sec_check = data_c.get("sector_check", {})
            if sec_check:
                dec = sec_check.get("declared_sector") or "None"
                st.write(f"**Declared Sector:** {dec} | **Sector Model Check:** {sec_check.get('note', '')}")

            aspects = data_c.get("aspect_findings", [])
            st.markdown("#### 8 Business Dimension Aspect Analysis")
            st.caption("No numeric score exists. 'Not stated' means the pitch text omitted that detail, not that it is a confirmed weakness.")

            cols_c = st.columns(2)
            for idx, a in enumerate(aspects):
                target_col = cols_c[idx % 2]
                status_key = a.get("status", "not_stated")
                icon_a, badge_text, badge_bg = ASPECT_ICONS.get(status_key, ("⬜", status_key, "#f5f5f5"))
                with target_col:
                    st.markdown(
                        f"""
                        <div style="background:{badge_bg};border:1px solid #ddd;border-radius:6px;padding:10px 14px;margin-bottom:10px;">
                            <div style="font-weight:600;font-size:0.95rem;">{icon_a} {a.get('aspect')} &nbsp;<span style="font-size:0.8rem;background:#fff;padding:2px 8px;border-radius:4px;border:1px solid #ccc;">{badge_text}</span></div>
                            <div style="font-size:0.85rem;color:#444;margin-top:4px;">{a.get('note', '')}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    evidence_list = a.get("evidence", [])
                    if evidence_list:
                        with st.expander("View Quoted Evidence Sentences"):
                            for ev in evidence_list:
                                st.markdown(f"> *\"{ev}\"*")

            vague = data_c.get("vague_terms", [])
            if vague:
                st.markdown("#### 💬 Vague Terms / Buzzwords Detected")
                st.caption("These buzzwords were identified in the pitch without supporting operational metrics:")
                st.write(", ".join(f"`{v}`" for v in vague))

            missing_q = data_c.get("missing_information_questions", [])
            if missing_q:
                with st.expander(f"❓ Clarifying Questions to Address Gaps ({len(missing_q)})"):
                    for q in missing_q:
                        st.markdown(f"- **{q.get('aspect', 'Aspect')}**: {q.get('question')}")

        st.markdown("---")

        # SECTION 5: Model D (Multilabel Failure Category Classifier)
        st.markdown("### Section 5: Failure Categories and Historical Post-Mortem Evidence (Model D)")
        env_d = models.get("model_d", {})
        if not env_d or env_d.get("status") != "ok":
            st.markdown(not_applicable_card("Model D", env_d.get("applicability_reason", "No category data.")), unsafe_allow_html=True)
        else:
            data_d = env_d.get("data", {})
            ood = data_d.get("ood", {})
            if ood.get("flagged"):
                st.markdown(ood_banner("Model D"), unsafe_allow_html=True)

            st.caption(data_d.get("meaning", "Probabilities indicate resemblance to past post-mortem narratives, not a certainty of failure."))

            cats = data_d.get("categories", [])
            for c in cats:
                cat_label = c.get("label", c.get("category"))
                is_supported = c.get("supported", True)
                prob = c.get("probability", 0.0)
                thresh = c.get("threshold", 0.5)
                pred = c.get("predicted", False)

                col_d1, col_d2 = st.columns([3, 1])
                with col_d1:
                    if not is_supported:
                        st.markdown(f"**{cat_label}** *(Not modelled due to insufficient training post-mortems)*")
                    else:
                        tag = "🚨 THEME FLAGGED" if pred else "Normal"
                        st.markdown(f"**{cat_label}** — `{prob*100:.1f}%` similarity *(threshold: {thresh*100:.1f}%)* — **{tag}**")
                        st.progress(float(prob))
                        ev_sent = c.get("evidence_sentence")
                        if ev_sent:
                            st.caption(f"Representative quote: *\"{ev_sent}\"*")

                with col_d2:
                    sim_cases = c.get("similar_historical_failures", [])
                    if sim_cases:
                        with st.expander(f"Past Cases ({len(sim_cases)})"):
                            for sc in sim_cases:
                                st.markdown(f"• **{sc.get('name', 'Startup')}** ({sc.get('year', '')}): {sc.get('reason', '')}")

        st.markdown("---")

        # SECTION 6: Key Factors
        st.markdown("### Section 6: Key Contributing Factors Across All Models")
        st.caption("Synthesis of the most prominent quantitative and qualitative signals driving the evaluation.")
        if key_factors:
            for m_key, f_list in key_factors.items():
                if f_list:
                    st.markdown(f"#### {m_key.replace('_', ' ').title()}")
                    for item in f_list:
                        st.json(item, expanded=False)
        else:
            st.info("No specific key factors extracted.")

        st.markdown("---")

        # SECTION 7: Assumptions, Uncertainty & Limitations
        st.markdown("### Section 7: Assumptions, Uncertainty & Limitations")
        st.caption("Uncertainty is always visible. Models provide statistical approximations from historical records.")
        with st.expander("Open Trust & Confidence Details", expanded=True):
            warnings_list = trust.get("warnings", [])
            if warnings_list:
                st.markdown("**Active Warnings:**")
                for w in warnings_list:
                    st.warning(w)

            st.markdown("**General Model Limitations:**")
            for lim in trust.get("general_limitations", []):
                st.markdown(f"- {lim}")

        st.markdown("---")

        # SECTION 8: Overall Assessment and Next Steps
        st.markdown("### Section 8: Overall Assessment and Next Steps")
        st.success(f"**Final Diagnostic:** {interpretation.get('category')} — {interpretation.get('summary')}")
        st.info("Prioritized tactical recommendations are available in the **Recommendations** tab.")

    # ═════════════════════════════════════════════════════════════════════════════
    # TAB 2: RECOMMENDATIONS (Step 3/4 Activation)
    # ═════════════════════════════════════════════════════════════════════════════
    with tab_recs:
        st.markdown("### 💡 Strategic Advisory & Playbook Recommendations")
        st.info("🚧 **Recommendations Engine Coming Soon** (Step 3/4 Activation)")
        st.markdown(
            """
            In the upcoming release, this section will generate:
            - **Prioritized tactical action items** tailored specifically to the failure themes detected by Model D and gaps identified by Model C.
            - **Implementation steps, expected benefits, and validation metrics** for each action.
            - **Curated case studies from the startup failure playbook** matching your exact industry and operational stage.
            - **Interactive clarification Q&A** allowing you to provide additional context and regenerate the recommendations.
            """
        )

        issues = report.get("issues", [])
        if issues:
            st.markdown(f"#### Identified Hurdle Candidates for Advisory ({len(issues)})")
            for iss in issues:
                st.markdown(
                    f"- **[{iss.get('source')}] {iss.get('title')}** *(Severity: {iss.get('severity')})*: {iss.get('evidence') or ''}"
                )

    # ═════════════════════════════════════════════════════════════════════════════
    # TAB 3: TRUST & LIMITATIONS
    # ═════════════════════════════════════════════════════════════════════════════
    with tab_trust:
        st.markdown("### 🛡 Trust Panel, Provenance & Validation Metrics")
        
        # Currency conversion details
        curr = trust.get("currency_conversion", {})
        if curr:
            st.markdown("#### 💱 Currency Conversion Details")
            st.write(f"- **Declared Funding:** {curr.get('original')}")
            st.write(f"- **USD Equivalent:** {curr.get('converted_usd')}")
            st.write(f"- **Exchange Rate Used:** `{curr.get('rate')}` *(As of {curr.get('date')})*")

        # Provenance
        prov = trust.get("provenance", {})
        if prov:
            st.markdown("#### 📝 Field Provenance Tracking")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Fields Provided by User:**")
                for f in prov.get("provided_fields", []):
                    st.write(f"✓ `{f}`")
            with c2:
                st.markdown("**Fields Left Blank (Not Stated):**")
                for f in prov.get("missing_fields", []):
                    st.write(f"○ `{f}`")

        # Validation status
        val_status = trust.get("validation_status", {})
        if val_status:
            st.markdown("#### 🧪 Model Offline Validation Status")
            st.json(val_status, expanded=False)

