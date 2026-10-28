"""
Startup Evaluation — Main Streamlit Application.

Page flow managed via st.session_state["page"]:
  landing → form → review → processing → report

Run with:
  BACKEND_URL=http://localhost:8000 streamlit run frontend/app.py
"""
import streamlit as st
from frontend import api_client

st.set_page_config(
    page_title="Startup Evaluation",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session-state initialisation ──────────────────────────────────────────────
DEFAULTS = {
    "page": "landing",
    "step": 1,
    # form fields — step 1
    "f_idea": "",
    "f_problem": "",
    "f_customer": "",
    # step 2
    "f_industry": "",
    "f_country": "",
    "f_state": "",
    "f_target_market": "global",
    "f_business_model": [],
    # step 3
    "f_stage": "idea",
    "f_funding_raised": 0.0,
    "f_currency": "USD",
    "f_budget": 0.0,
    "f_funding_rounds": 0,
    "f_investor_types": [],
    "f_rounds_reached": [],
    # step 4
    "f_team_size": 1,
    "f_team_skills": [],
    "f_founder_experience": "first-time",
    # step 5
    "f_validation": "",
    "f_competitors": "",
    "f_traction": "",
    # optional model-A fields
    "f_homepage_url": "",
    "f_city": "",
    "f_region": "",
    "f_founded_at": "",
    "f_first_funding_at": "",
    "f_last_funding_at": "",
    # evaluation
    "eval_id": None,
    "validate_result": None,
    "report": None,
    "options": None,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def goto(page: str, step: int = 1):
    st.session_state["page"] = page
    st.session_state["step"] = step
    st.rerun()


def start_over():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.rerun()


# ── Load options once ─────────────────────────────────────────────────────────
if st.session_state["options"] is None:
    opts = api_client.fetch_options()
    st.session_state["options"] = opts if opts else {}

opts = st.session_state["options"]

# ── Route ─────────────────────────────────────────────────────────────────────
page = st.session_state["page"]

if page == "landing":
    from frontend.pages import page_landing
    page_landing.render(goto)

elif page == "form":
    from frontend.pages import page_form
    page_form.render(goto, opts, start_over)

elif page == "review":
    from frontend.pages import page_review
    page_review.render(goto, start_over)

elif page == "processing":
    from frontend.pages import page_processing
    page_processing.render(goto)

elif page == "report":
    from frontend.pages import page_report
    page_report.render(goto, start_over)

elif page == "about":
    from frontend.pages import page_about
    page_about.render(goto)

