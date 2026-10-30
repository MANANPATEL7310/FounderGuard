"""Review page: calls /validate, shows coverage + warnings, then submits."""
from __future__ import annotations
import streamlit as st
from frontend import api_client
from frontend.ui_helpers import RISK_COLORS


def _build_payload() -> dict:
    s = st.session_state

    # Safe country extraction (handles both string and dict formats)
    raw_country = s.get("f_country", "USA")
    if isinstance(raw_country, dict):
        country_code = raw_country.get("code") or raw_country.get("name") or "USA"
    else:
        country_code = str(raw_country or "USA").strip()

    # Safe state extraction
    raw_state = s.get("f_state")
    if isinstance(raw_state, dict):
        state_code = raw_state.get("code") or raw_state.get("name")
    else:
        state_code = str(raw_state).strip() if raw_state else None

    # Safe currency extraction
    raw_curr = s.get("f_currency", "USD")
    if isinstance(raw_curr, dict):
        curr_code = raw_curr.get("code", "USD")
    else:
        curr_code = str(raw_curr or "USD").strip()

    payload = {
        "idea_description": s["f_idea"],
        "problem_statement": s["f_problem"] or None,
        "target_customer": s["f_customer"] or None,
        "industry": s["f_industry"],
        "country": country_code,
        "state": state_code,
        "target_market": s["f_target_market"],
        "business_model": s["f_business_model"],
        "stage": s["f_stage"],
        "budget_available": s["f_budget"] if s["f_budget"] > 0 else None,
        "funding_raised": s["f_funding_raised"],
        "currency": curr_code,
        "funding_rounds": s["f_funding_rounds"],
        "investor_types": s["f_investor_types"],
        "rounds_reached": s["f_rounds_reached"],
        "team_size": s["f_team_size"],
        "team_skills": s["f_team_skills"],
        "founder_experience": s["f_founder_experience"],
        "validation_evidence": s["f_validation"] or None,
        "competitors": s["f_competitors"] or None,
        "traction": s["f_traction"] or None,
        "homepage_url": s["f_homepage_url"] or None,
        "city": s["f_city"] or None,
        "region": s["f_region"] or None,
        "founded_at": s["f_founded_at"] or None,
        "first_funding_at": s["f_first_funding_at"] or None,
        "last_funding_at": s["f_last_funding_at"] or None,
        "consent": True,
    }
    return payload


def render(goto, start_over):
    st.title("🔍 Review Your Submission")
    st.caption("Check the details below before running the evaluation. This is your last chance to edit.")

    with st.sidebar:
        if st.button("🔄 Start Over", key="review_sidebar_start_over"):
            start_over()

    payload = _build_payload()

    # ── Validate against backend ──────────────────────────────────────────────
    if st.session_state.get("validate_result") is None:
        with st.spinner("Validating with backend…"):
            ok, result = api_client.validate_submission(payload)
        if not ok:
            detail = result.get("detail", "Unknown validation error.")
            st.error(f"Validation failed: {detail}")
            col1, col2 = st.columns(2)
            if col1.button("← Edit", key="review_val_err_edit"):
                goto("form", step=5)
            if col2.button("🔄 Start Over", key="review_val_err_start_over"):
                start_over()
            return
        st.session_state["validate_result"] = result

    vr = st.session_state["validate_result"]
    norm = vr.get("normalized", {})
    applicability = vr.get("models_applicability", {})
    warnings = vr.get("warnings", [])

    # ── Submission summary ────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 📋 Idea")
        st.write(st.session_state["f_idea"][:300] + ("…" if len(st.session_state["f_idea"]) > 300 else ""))

        st.markdown("#### 🏭 Classification")
        st.write(f"**Industry:** {norm.get('industry', '—')}")
        st.write(f"**Country:** {norm.get('country', '—')}  |  **State:** {norm.get('state') or '—'}")
        st.write(f"**Stage:** {norm.get('stage', '—')}")

    with col_right:
        st.markdown("#### 💰 Funding")
        orig = norm.get("original_funding", 0)
        orig_cur = norm.get("original_currency", "USD")
        usd = norm.get("funding_total_usd", 0)
        rate = norm.get("exchange_rate_used", 1.0)
        rate_date = norm.get("exchange_rate_date", "—")
        rounds = norm.get("funding_rounds", 0)

        if orig > 0:
            st.write(f"**Raised:** {orig_cur} {orig:,.0f}")
            st.write(f"**Converted:** USD {usd:,.2f}  *(rate: {rate} — {rate_date})*")
            st.write(f"**Rounds:** {rounds}")
        else:
            st.write("No external funding entered.")

        st.markdown("#### 👥 Team")
        st.write(f"**Size:** {st.session_state['f_team_size']}")
        st.write(f"**Skills:** {', '.join(st.session_state['f_team_skills']) or '—'}")
        st.write(f"**Experience:** {st.session_state['f_founder_experience']}")

    # ── Model coverage preview ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🤖 Which models will run?")

    model_labels = {
        "model_a": "A — Outcome Classifier (CatBoost)",
        "model_b": "B — Risk Estimator (LogisticRegression)",
        "model_c": "C — Idea Evaluator (BiGRU NLP)",
        "model_d": "D — Failure Categories (Multilabel LR)",
    }
    cols = st.columns(4)
    for i, (mid, label) in enumerate(model_labels.items()):
        app_info = applicability.get(mid, {})
        applicable = app_info.get("applicable", True)
        reason = app_info.get("reason", "")
        with cols[i]:
            if applicable:
                st.success(f"✅ {label.split('—')[0]}")
                st.caption(label.split("—")[1].strip())
            else:
                st.warning(f"⊘ {label.split('—')[0]}")
                st.caption(reason)

    # ── Warnings ──────────────────────────────────────────────────────────────
    if warnings:
        st.markdown("---")
        st.markdown("#### ⚠ Validation Warnings")
        for w in warnings:
            st.warning(w)

    # ── Provenance ────────────────────────────────────────────────────────────
    provided = norm.get("provenance_provided_fields", [])
    missing = norm.get("provenance_missing_fields", [])
    with st.expander(f"📊 Field provenance ({len(provided)} provided, {len(missing)} not provided)"):
        col_p, col_m = st.columns(2)
        col_p.markdown("**Provided**")
        for f in provided:
            col_p.write(f"✓ {f}")
        col_m.markdown("**Not provided** *(blank = not stated, never negative)*")
        for f in missing:
            col_m.write(f"○ {f}")

    # ── Edit / Submit ─────────────────────────────────────────────────────────
    st.markdown("---")
    col_edit, col_submit = st.columns([2, 3])

    with col_edit:
        if st.button("← Edit Submission", key="review_bottom_edit_btn", use_container_width=True):
            st.session_state["validate_result"] = None
            goto("form", step=5)

    with col_submit:
        if st.button("🚀 Submit for Evaluation", key="review_bottom_submit_btn", type="primary", use_container_width=True):
            with st.spinner("Submitting…"):
                ok, resp = api_client.submit_evaluation(payload)
            if ok:
                st.session_state["eval_id"] = resp["evaluation_id"]
                st.session_state["validate_result"] = None
                goto("processing")
            else:
                st.error(f"Submission failed: {resp.get('detail', 'Unknown error')}")

