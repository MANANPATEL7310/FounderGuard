"""
Startup Evaluation — Main Streamlit Application.

Page flow managed via st.session_state["page"]:
  landing → form → review → processing → report

Run with:
  BACKEND_URL=http://localhost:8000 streamlit run frontend/app.py
"""
import sys
import importlib
from pathlib import Path

# Ensure workspace root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from frontend import api_client

st.set_page_config(
    page_title="Startup Evaluation",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global Modern Styling ─────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1180px !important;
    }

    .fg-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 18px;
        backdrop-filter: blur(8px);
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .fg-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
    }

    .hero-title {
        background: linear-gradient(135deg, #F8FAFC 0%, #94A3B8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.75rem !important;
        font-weight: 800 !important;
        line-height: 1.15;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(99, 102, 241, 0.15);
        color: #A5B4FC;
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    div.stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.55rem 1.25rem !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        transition: all 0.2s ease !important;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4) !important;
    }

    div.stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.6) !important;
        transform: translateY(-1px);
    }

    [data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 800 !important;
    }

    section[data-testid="stSidebar"] {
        background: #0F172A !important;
        border-right: 1px solid rgba(148, 163, 184, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

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

# ── Defensively sanitize stale session state from earlier runs ────────────────
if isinstance(st.session_state.get("f_country"), dict):
    st.session_state["f_country"] = st.session_state["f_country"].get("code", "USA")
if isinstance(st.session_state.get("f_currency"), dict):
    st.session_state["f_currency"] = st.session_state["f_currency"].get("code", "USD")
if isinstance(st.session_state.get("f_state"), dict):
    st.session_state["f_state"] = st.session_state["f_state"].get("code", "")

# ── Route ─────────────────────────────────────────────────────────────────────
page = st.session_state["page"]

if page == "landing":
    from frontend.pages import page_landing
    importlib.reload(page_landing)
    page_landing.render(goto)

elif page == "form":
    from frontend.pages import page_form
    importlib.reload(page_form)
    page_form.render(goto, opts, start_over)

elif page == "review":
    from frontend.pages import page_review
    importlib.reload(page_review)
    page_review.render(goto, start_over)

elif page == "processing":
    from frontend.pages import page_processing
    importlib.reload(page_processing)
    page_processing.render(goto)

elif page == "report":
    from frontend.pages import page_report
    importlib.reload(page_report)
    page_report.render(goto, start_over)

elif page == "about":
    from frontend.pages import page_about
    importlib.reload(page_about)
    page_about.render(goto)

