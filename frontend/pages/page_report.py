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
    raw_eval_id = st.session_state.get("eval_id")

    # If no eval_id in state, return early
    if not raw_eval_id:
        st.error("No evaluation ID available.")
        if st.button("← Return to Start"):
            start_over()
        return

    eval_id: str = str(raw_eval_id)

    # If no report loaded, try to fetch it
    if not report:
        report = api_client.get_report(eval_id)
        if report:
            st.session_state["report"] = report

    if not report:
        st.error("No report available to display.")
        if st.button("← Return to Start"):
            start_over()
        return

    meta = report.get("meta") or {}
    input_sum = report.get("input_summary") or {}
    models = report.get("models") or {}
    interpretation = report.get("interpretation") or {}
    trust = report.get("trust") or {}
    key_factors = report.get("key_factors") or {}
    raw_sections = report.get("sections") or []
    sections = {s["section_number"]: s for s in raw_sections if isinstance(s, dict) and "section_number" in s}

    # Pre-fetch export formats for both Sidebar and Top/Bottom Action Bars
    ok_json, json_bytes, _ = api_client.export_report(eval_id, "json")
    ok_html, html_bytes, _ = api_client.export_report(eval_id, "html")
    ok_pdf, pdf_bytes, _ = api_client.export_report(eval_id, "pdf")

    # ── Sidebar Controls ──────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Actions & Exports")
        st.caption("Export evaluation data, switch versions, or purge records.")
        st.write(f"**ID:** `{meta.get('evaluation_id', eval_id)}`")
        st.write(f"**Completed:** {meta.get('completed_at', '—')[:19].replace('T', ' ')}")

        st.markdown("---")
        st.markdown("#### Download Report")
        if ok_json and json_bytes is not None:
            st.download_button("Download JSON Report", data=json_bytes, file_name=f"report_{eval_id}.json", mime="application/json", key="sb_dl_json_btn", use_container_width=True)
        if ok_html and html_bytes is not None:
            st.download_button("Download HTML Report", data=html_bytes, file_name=f"report_{eval_id}.html", mime="text/html", key="sb_dl_html_btn", use_container_width=True)
        if ok_pdf and pdf_bytes is not None:
            st.download_button("Download PDF Report", data=pdf_bytes, file_name=f"report_{eval_id}.pdf", mime="application/pdf", key="sb_dl_pdf_btn", use_container_width=True)

        st.markdown("---")
        st.markdown("#### Navigation")
        if st.button("Return to Home", key="sb_nav_home_btn", type="primary", use_container_width=True):
            start_over()
        if st.button("Start New Evaluation", key="sb_nav_new_eval_btn", use_container_width=True):
            start_over()
        if st.button("About the Models", key="sb_nav_about_btn", use_container_width=True):
            goto("about")

        # Lineage / Version Switcher (Section 3.8)
        status_data = api_client.get_status(eval_id)
        available_versions = status_data.get("available_versions", []) if status_data else []
        if len(available_versions) > 1:
            st.markdown("---")
            st.markdown("#### Evaluation Versions")
            version_labels = {v["evaluation_id"]: f"v{v.get('version', 1)} ({v.get('evaluation_id')[-8:]})" for v in available_versions}
            curr_idx = list(version_labels.keys()).index(eval_id) if eval_id in version_labels else 0
            selected_v = st.selectbox(
                "Select Version to View:",
                options=list(version_labels.keys()),
                format_func=lambda x: version_labels.get(x, x),
                index=curr_idx,
                key="sb_version_selector",
            )
            if selected_v != eval_id:
                st.session_state["eval_id"] = selected_v
                st.session_state["report"] = None
                st.rerun()

        st.markdown("---")
        st.markdown("#### Privacy & Data")
        if st.button("Delete Evaluation Data", key="sb_delete_data_btn", type="secondary", use_container_width=True):
            if eval_id:
                api_client.delete_evaluation(eval_id)
            st.success("Your evaluation data has been deleted.")
            start_over()

    # ── Header ──────────────────────────────────────────────────────────────────
    pitch = input_sum.get("idea_description", "")
    title = pitch.split("\n")[0][:100] if pitch else "Startup Pitch Evaluation"
    st.title(f"{title}")
    st.caption(
        f"Stage: **{input_sum.get('stage', '—')}** | "
        f"Industry: **{input_sum.get('industry', '—')}** | "
        f"Location: **{input_sum.get('country', '—')} {input_sum.get('state') or ''}** | "
        f"Report ID: `{meta.get('evaluation_id', eval_id)}`"
    )

    # ── Top Download & Navigation Toolbar ─────────────────────────────────────────
    st.markdown(
        """
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px 18px; margin: 12px 0 18px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:600; font-size:0.92rem; color:#0F172A;">
                    Report Exports & Actions
                </span>
                <span style="font-size:0.8rem; color:#64748B;">
                    Options also available in the left sidebar
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    m_c1, m_c2, m_c3, m_c4, m_c5 = st.columns([1.5, 1.2, 1.2, 1.2, 1.3])
    with m_c1:
        if st.button("Home", key="main_top_nav_home", type="primary", use_container_width=True):
            start_over()
    with m_c2:
        if ok_json and json_bytes is not None:
            st.download_button("Download JSON", data=json_bytes, file_name=f"report_{eval_id}.json", mime="application/json", key="main_top_dl_json", use_container_width=True)
    with m_c3:
        if ok_html and html_bytes is not None:
            st.download_button("Download HTML", data=html_bytes, file_name=f"report_{eval_id}.html", mime="text/html", key="main_top_dl_html", use_container_width=True)
    with m_c4:
        if ok_pdf and pdf_bytes is not None:
            st.download_button("Download PDF", data=pdf_bytes, file_name=f"report_{eval_id}.pdf", mime="application/pdf", key="main_top_dl_pdf", use_container_width=True)
    with m_c5:
        if st.button("New Evaluation", key="main_top_new_eval", use_container_width=True):
            start_over()

    # ── Overall Interpretation Banner ───────────────────────────────────────────
    cat = interpretation.get("category", "Mixed picture")
    icon, bg_color = INTERP_ICONS.get(cat, ("[Diagnostic]", "#F8FAFC"))
    st.markdown(
        f"""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-left:4px solid #0F172A;padding:18px 24px;border-radius:6px;margin:12px 0 24px 0;">
            <div style="font-size:1.15rem;font-weight:700;color:#0F172A;margin-bottom:6px;">Overall Evaluation: {cat}</div>
            <div style="font-size:0.92rem;color:#334155;margin-bottom:10px;line-height:1.5;">{interpretation.get('summary', '')}</div>
            <ul style="margin:0;padding-left:20px;font-size:0.88rem;color:#475569;line-height:1.6;">
                {''.join(f'<li>{r}</li>' for r in interpretation.get('reasons', []))}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Prominent pill navigation makes all report sections discoverable immediately.
    tab_report, tab_recs, tab_trust = st.tabs([
        "◈  Evaluation Report",
        "✦  Recommendations",
        "◌  Trust & Limitations",
    ])

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
                        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:6px;padding:12px 16px;margin-bottom:10px;">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <span style="font-weight:600;font-size:0.95rem;color:#0F172A;">{a.get('aspect')}</span>
                                <span style="font-size:0.75rem;font-weight:600;background:#FFFFFF;color:#334155;padding:2px 8px;border-radius:4px;border:1px solid #CBD5E1;">{badge_text}</span>
                            </div>
                            <div style="font-size:0.85rem;color:#475569;margin-top:6px;line-height:1.4;">{a.get('note', '')}</div>
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
                st.markdown("#### Vague Terms and Buzzwords Detected")
                st.caption("These terms were identified in the pitch without supporting operational metrics:")
                st.write(", ".join(f"`{v}`" for v in vague))

            missing_q = data_c.get("missing_information_questions", [])
            if missing_q:
                with st.expander(f"Clarifying Questions to Address Gaps ({len(missing_q)})"):
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
                        if isinstance(item, dict):
                            if "feature" in item:
                                feat = item.get("feature", "Feature")
                                val = item.get("value", "")
                                effect = item.get("effect_on_probability") or item.get("importance")
                                direction = item.get("direction", "")
                                eff_str = f" | Effect: `{effect:+.4f}`" if isinstance(effect, float) else (f" | Importance: `{effect}`" if effect is not None else "")
                                dir_icon = "🔺 " if "raise" in direction.lower() else ("🔻 " if "lower" in direction.lower() else "📊 ")
                                dir_str = f" ({direction})" if direction else ""
                                val_str = f" (Value: `{val}`)" if val is not None and str(val).strip() != "" else ""
                                st.markdown(f"- {dir_icon}**{feat}**{val_str}{eff_str}{dir_str}")
                            elif "term" in item:
                                term = item.get("term", "")
                                st.markdown(f"- 🏷️ **Attended Concept:** `{term}`")
                            elif "category" in item:
                                cat = item.get("category", "")
                                prob = item.get("probability", 0)
                                ev = item.get("evidence", "")
                                prob_pct = f"{prob * 100:.1f}%" if isinstance(prob, (int, float)) else str(prob)
                                ev_text = f" — *\"{ev}\"*" if ev else ""
                                st.markdown(f"- ⚠️ **{cat}** (Failure Risk Pattern: `{prob_pct}`){ev_text}")
                            else:
                                parts = [f"**{k.replace('_', ' ').title()}:** {v}" for k, v in item.items()]
                                st.markdown(f"- {' | '.join(parts)}")
                        else:
                            st.markdown(f"- {item}")
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

        st.markdown("---")
        st.markdown("### 🏁 Evaluation Completed — Quick Navigation & Exports")
        st.caption("Download your report now or return to the home screen to test another startup idea.")
        bot_c1, bot_c2, bot_c3, bot_c4, bot_c5 = st.columns([1.5, 1.2, 1.2, 1.2, 1.3])
        with bot_c1:
            if st.button("🏠 Return to Home", key="rep_bottom_nav_home", type="primary", use_container_width=True):
                start_over()
        with bot_c2:
            if ok_json and json_bytes is not None:
                st.download_button("📄 Download JSON", data=json_bytes, file_name=f"report_{eval_id}.json", mime="application/json", key="rep_bottom_dl_json", use_container_width=True)
        with bot_c3:
            if ok_html and html_bytes is not None:
                st.download_button("🌐 Download HTML", data=html_bytes, file_name=f"report_{eval_id}.html", mime="text/html", key="rep_bottom_dl_html", use_container_width=True)
        with bot_c4:
            if ok_pdf and pdf_bytes is not None:
                st.download_button("📑 Download PDF", data=pdf_bytes, file_name=f"report_{eval_id}.pdf", mime="application/pdf", key="rep_bottom_dl_pdf", use_container_width=True)
        with bot_c5:
            if st.button("🗑️ Delete Data", key="rep_bottom_del_data", use_container_width=True):
                if eval_id:
                    api_client.delete_evaluation(eval_id)
                st.success("Your evaluation data has been deleted.")
                start_over()

    # ═════════════════════════════════════════════════════════════════════════════
    # TAB 2: RECOMMENDATIONS (Step 3: Template Playbook / Step 4: LLM)
    # ═════════════════════════════════════════════════════════════════════════════
    with tab_recs:
        st.markdown("### Prioritized Strategic Recommendations")

        # Fetch recommendations from backend
        rec_data = api_client.get_recommendations(meta.get("evaluation_id", eval_id))

        if not rec_data or not rec_data.get("recommendations"):
            st.info("Recommendations are being generated or no recommendations available.")
        else:
            if rec_data.get("is_fallback"):
                st.markdown(
                    """
                    <div style="border-left:4px solid #475569;background:#F8FAFC;padding:14px 18px;border:1px solid #E2E8F0;border-radius:6px;margin:12px 0 16px 0;">
                        <strong style="color:#0F172A;font-size:0.95rem;">Playbook Reference Recommendations (Template-Based)</strong><br>
                        <span style="font-size:0.88rem;color:#475569;display:inline-block;margin-top:4px;line-height:1.5;">
                            These recommendations are synthesized deterministically from our curated startup failure playbook
                            using the prioritized risk signals from Models A, B, C, and D.
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            recs = rec_data.get("recommendations", [])

            # Priority filter
            prio_filter = st.radio("Filter by Priority:", ["All", "High", "Medium", "Low"], horizontal=True)
            filtered_recs = [r for r in recs if prio_filter == "All" or r.get("priority") == prio_filter]

            prio_styles = {
                "High": ("High Priority", "#FEF2F2", "#DC2626", "#FEE2E2", "#991B1B"),
                "Medium": ("Medium Priority", "#FFFBEB", "#D97706", "#FEF3C7", "#92400E"),
                "Low": ("Low Priority", "#F0FDF4", "#16A34A", "#DCFCE7", "#166534"),
            }

            st.write(f"Showing **{len(filtered_recs)}** of **{len(recs)}** prioritized recommendations:")

            for r in filtered_recs:
                p_label, p_bg, p_border, p_badge_bg, p_badge_text = prio_styles.get(
                    r.get("priority", "Medium"),
                    ("Priority", "#F8FAFC", "#94A3B8", "#F1F5F9", "#334155")
                )

                why_raw = str(r.get('why_it_matters_for_this_startup') or "")
                if "{'text':" in why_raw or '{"text":' in why_raw:
                    import re
                    m = re.search(r"['\"]text['\"]\s*:\s*['\"]([^'\"]+)['\"]", why_raw)
                    if m:
                        why_raw = re.sub(r"\{['\"]text['\"].*?\}", f"\"{m.group(1)}\"", why_raw)

                with st.container():
                    st.markdown(
                        f"""
                        <div style="background:{p_bg};border:1px solid #E2E8F0;border-left:4px solid {p_border};border-radius:6px;padding:16px 20px;margin-bottom:14px;">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <span style="font-weight:700;font-size:1.05rem;color:#0F172A;">{r.get('identified_problem_or_risk')}</span>
                                <span style="background:{p_badge_bg};color:{p_badge_text};border:1px solid {p_border};padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:600;">{p_label}</span>
                            </div>
                            <div style="font-size:0.9rem;color:#334155;margin:8px 0 12px 0;line-height:1.5;">
                                <strong style="color:#0F172A;">Why it matters:</strong> {why_raw}
                            </div>
                            <div style="background:#FFFFFF;padding:12px 14px;border-radius:6px;border:1px solid #E2E8F0;margin-bottom:4px;">
                                <strong style="color:#0F172A;">Specific Action:</strong> <span style="color:#1E293B;">{r.get('specific_action')}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    with st.expander(f"View Implementation Steps & Validation Method ({r.get('identified_problem_or_risk')})", expanded=False):
                        st.markdown("**Implementation Steps:**")
                        for s_idx, step in enumerate(r.get("implementation_steps", []), 1):
                            st.markdown(f"{s_idx}. {step}")

                        st.markdown(f"**Expected Benefit:** {r.get('expected_benefit')}")
                        st.markdown(f"**Validation Metric & Target:** `{r.get('validation_method')}`")

                        col_ref1, col_ref2 = st.columns(2)
                        with col_ref1:
                            st.caption(f"Evidence References: `{', '.join(r.get('evidence_refs', [])) or 'Input pitch'}`")
                        with col_ref2:
                            st.caption(f"Playbook References: `{', '.join(r.get('playbook_refs', []))}`")

                        # Local action checklist
                        action_key = f"action_done_{r.get('id')}"
                        st.checkbox("Mark this action as completed in workplan", key=action_key)

                    st.markdown("")

            # Clarifying Questions & Clarification Loop (Section 3.8 & 5.11)
            questions = rec_data.get("clarifying_questions", [])
            if questions:
                st.markdown("---")
                st.markdown(f"#### ❓ Clarifying Questions & Feedback Loop ({len(questions)})")
                st.caption(
                    "Addressing these questions creates a new linked version of your evaluation, "
                    "re-evaluates narrative risk signals, and personalizes the recommendations."
                )

                with st.form(key=f"clarification_form_{eval_id}"):
                    answers = []
                    for idx, q in enumerate(questions[:5]):
                        q_aspect = q.get("aspect", "Context")
                        q_text = q.get("question", "")
                        st.markdown(f"**{idx + 1}. [{q_aspect}]** {q_text}")
                        if q.get("reason_it_matters"):
                            st.caption(f"*{q.get('reason_it_matters')}*")
                        ans_val = st.text_input(
                            f"Your clarification for {q_aspect}:",
                            key=f"q_input_{eval_id}_{idx}",
                            placeholder="Provide metrics, details, or operational facts...",
                            label_visibility="collapsed",
                        )
                        ans_str = str(ans_val or "").strip()
                        answers.append({
                            "aspect": q_aspect,
                            "question": q_text,
                            "answer": ans_str,
                        })

                    st.markdown("")
                    clarif_submitted = st.form_submit_button("Submit Clarifications & Generate New Version 🚀", use_container_width=True)

                    if clarif_submitted:
                        valid_answers = [a for a in answers if a["answer"]]
                        if not valid_answers:
                            st.warning("Please provide at least one answer before submitting clarifications.")
                        else:
                            with st.spinner("Submitting clarifications and initiating re-evaluation..."):
                                ok, resp = api_client.submit_clarifications(eval_id, valid_answers)
                                if ok:
                                    st.session_state["eval_id"] = resp["evaluation_id"]
                                    st.session_state["report"] = None
                                    goto("processing")
                                else:
                                    st.error(resp.get("detail", "Failed to submit clarifications."))

            # Assumptions & Disclaimers
            assumptions = rec_data.get("assumptions", [])
            if assumptions:
                with st.expander("Recommendation Assumptions & Standing Disclaimer"):
                    st.markdown("**Assumptions made during analysis:**")
                    for asm in assumptions:
                        st.markdown(f"- {asm}")
                    st.markdown("---")
                    st.caption(rec_data.get("disclaimer", ""))

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
            for m_key, m_val in val_status.items():
                m_title = m_key.replace("_", " ").title()
                st.markdown(f"**{m_title} Components:**")
                if isinstance(m_val, dict):
                    for comp, status_str in m_val.items():
                        comp_name = comp.replace("_", " ").title()
                        is_ok = "validated" in str(status_str).lower() and "not validated" not in str(status_str).lower()
                        badge = "✅" if is_ok else "ℹ️"
                        st.markdown(f"- {badge} **{comp_name}:** {status_str}")
                else:
                    st.markdown(f"- ℹ️ {m_val}")
