"""Processing screen: polls backend status and transitions to report."""
from __future__ import annotations
import time
import streamlit as st
from frontend import api_client
from frontend.config import MAX_POLL_ATTEMPTS, POLL_INTERVAL_S


def render(goto):
    st.title("Analyzing Startup Submission")
    st.caption("Running four independent machine learning models and synthesizing the evaluation report.")

    eval_id = st.session_state.get("eval_id")
    if not eval_id:
        st.error("No evaluation ID found in session.")
        if st.button("Return to Home"):
            goto("landing")
        return

    st.markdown(f"**Evaluation ID:** `{eval_id}`")
    progress_bar = st.progress(0.2)
    status_placeholder = st.empty()
    details_placeholder = st.empty()

    # Poll status in loop or fragment
    attempts = 0
    poll_success = False

    while attempts < MAX_POLL_ATTEMPTS:
        attempts += 1
        stat = api_client.get_status(eval_id)

        if not stat:
            status_placeholder.warning("Waiting for backend response...")
            time.sleep(POLL_INTERVAL_S)
            continue

        current_status = stat.get("status")
        per_model = stat.get("per_model_status", {})

        # Display progress info
        status_placeholder.markdown(f"**Current Status:** `{current_status}` | **Stage:** `{stat.get('stage', 'processing')}`")

        # Per-model status indicators
        cols = details_placeholder.columns(4)
        model_names = {
            "model_a": "Model A (Outcome)",
            "model_b": "Model B (Risk)",
            "model_c": "Model C (Idea NLP)",
            "model_d": "Model D (Themes)",
        }
        for idx, (m_id, label) in enumerate(model_names.items()):
            m_stat = per_model.get(m_id, "running")
            with cols[idx]:
                if m_stat == "ok":
                    st.success(f"[Complete] {label}")
                elif m_stat == "not_applicable":
                    st.info(f"[N/A] {label}")
                elif m_stat in ("pending", "running"):
                    st.warning(f"[Running] {label}")
                else:
                    st.error(f"[Degraded] {label}")

        if current_status in ("report_ready", "complete"):
            progress_bar.progress(1.0)
            # Fetch report
            rep = api_client.get_report(eval_id)
            if rep:
                st.session_state["report"] = rep
                poll_success = True
                break
        elif current_status == "failed":
            st.error("Evaluation processing encountered an error on the backend.")
            break

        progress_pct = min(0.9, 0.2 + (attempts / MAX_POLL_ATTEMPTS) * 0.7)
        progress_bar.progress(progress_pct)
        time.sleep(POLL_INTERVAL_S)

    if poll_success:
        st.success("Evaluation ready! Loading report...")
        time.sleep(0.5)
        goto("report")
    else:
        st.error("Evaluation timed out or could not be finalized.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Retry Status Check"):
                st.rerun()
        with col2:
            if st.button("Return to Form"):
                goto("form", step=1)

