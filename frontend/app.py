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
    page_title="Startup Evaluation — FounderGuard AI",
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

# Appearance is a user preference, not part of a fresh evaluation reset.
if "ui_theme" not in st.session_state:
    st.session_state["ui_theme"] = "light"
if "theme_toggle" not in st.session_state:
    st.session_state["theme_toggle"] = False


def inject_global_styles(theme: str) -> None:
    """Apply the visual system without touching application behaviour."""
    is_dark = theme == "dark"
    palette = {
        "canvas": "#06171C" if is_dark else "#EFF8F7",
        "surface": "rgba(10, 39, 47, .72)" if is_dark else "rgba(255, 255, 255, .72)",
        "surface_alt": "rgba(16, 57, 66, .76)" if is_dark else "rgba(225, 244, 241, .70)",
        "ink": "#F0FFFF" if is_dark else "#123239",
        "muted": "#A9C9C9" if is_dark else "#5B777B",
        "line": "rgba(62, 185, 183, .32)" if is_dark else "rgba(10, 121, 125, .20)",
        "input_line": "rgba(82, 220, 213, .55)" if is_dark else "rgba(0, 117, 121, .42)",
        "accent": "#18D7CD" if is_dark else "#007D83",
        "accent_hover": "#00A89F" if is_dark else "#005E66",
        "accent_soft": "rgba(24, 215, 205, .16)" if is_dark else "rgba(0, 158, 159, .14)",
        "blue_soft": "rgba(37, 205, 220, .15)" if is_dark else "rgba(39, 193, 192, .13)",
        "bottom_tone": "rgba(12, 57, 65, .88)" if is_dark else "rgba(205, 239, 236, .88)",
        "shadow": "0 20px 55px rgba(0, 0, 0, .34)" if is_dark else "0 20px 48px rgba(11, 101, 105, .14)",
    }
    css_vars = "\n".join(f"--fg-{key}: {value};" for key, value in palette.items())
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

        :root {{ {css_vars} }}
        html, body, [data-testid="stAppViewContainer"] {{
            background: var(--fg-canvas) !important;
            color: var(--fg-ink) !important;
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        .main {{ background:transparent !important; color:var(--fg-ink) !important; font-family:'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
        [data-testid="stAppViewContainer"] {{
            position:relative;
            isolation:isolate;
            background-image:radial-gradient(circle at 95% 1%, var(--fg-accent_soft), transparent 26rem), radial-gradient(circle at -4% 92%, var(--fg-blue_soft), transparent 31rem) !important;
        }}
        /* Keep the decorative layer independent of the app's native scroll container. */
        [data-testid="stApp"], .stApp {{ position:relative; z-index:1; overflow-y:auto !important; overflow-x:hidden !important; background:transparent !important; }}
        /* A calm tonal base sits behind the scrollable page; it is visual only, never a footer card. */
        .fg-bottom-tone {{
            position:fixed; z-index:0; pointer-events:none; left:-8vw; right:-8vw; bottom:-13rem; height:31rem;
            border-radius:50% 50% 0 0 / 14% 14% 0 0;
            background:linear-gradient(180deg, transparent 0%, var(--fg-blue_soft) 20%, var(--fg-bottom_tone) 58%, var(--fg-bottom_tone) 100%) !important;
        }}
        .fg-bottom-tone::after {{
            content:''; position:absolute; pointer-events:none; left:-5%; right:-5%; bottom:-3rem; height:20rem;
            border-radius:50% 50% 0 0 / 18% 18% 0 0;
            background:linear-gradient(180deg, transparent 0%, var(--fg-accent_soft) 45%, transparent 100%);
        }}
        [data-testid="stAppViewContainer"] .main, header[data-testid="stHeader"] {{ position:relative; z-index:1; }}
        #MainMenu, footer:not(.fg-site-footer) {{ visibility:hidden; }}
        footer.fg-site-footer {{ visibility:visible; }}
        button[data-testid="stBaseButton-header"] {{ display:none !important; }}
        header[data-testid="stHeader"], .stAppHeader {{ height:0 !important; min-height:0 !important; padding:0 !important; background:transparent !important; }}
        [data-testid="stToolbar"], [data-testid="stStatusWidget"] {{ display:none !important; }}
        .block-container {{
            max-width: 1180px !important;
            padding-top: 1.35rem !important;
            padding-bottom: 4rem !important;
        }}
        h1, h2, h3, h4, h5, h6, [data-testid="stHeadingWithActionElements"] h1, [data-testid="stHeadingWithActionElements"] h2 {{
            color: var(--fg-ink) !important;
            font-family: 'Manrope', 'DM Sans', sans-serif !important;
            font-weight: 800 !important;
            letter-spacing: -0.04em !important;
        }}
        h1 {{ font-size: clamp(2rem, 4vw, 3.35rem) !important; line-height: 1.08 !important; }}
        #landing-page-title {{ display:none !important; }}
        h2 {{ font-size: 1.62rem !important; }}
        h3 {{ font-size: 1.22rem !important; }}
        p, li, [data-testid="stMarkdownContainer"] {{ color: var(--fg-ink); }}
        .stCaption, [data-testid="stCaptionContainer"] {{ color: var(--fg-muted) !important; }}

        /* Brand header */
        .fg-brand {{ display:flex; align-items:center; gap:.72rem; min-height:3rem; }}
        .fg-brand-mark {{
            width:2.25rem; height:2.25rem; display:grid; place-items:center; border-radius:.82rem;
            color:#FFFFFF; background:linear-gradient(135deg, var(--fg-accent), #0A9DCB);
            box-shadow:0 8px 18px rgba(0, 139, 146, .28); font-family:'Manrope',sans-serif; font-size:1.05rem; font-weight:800;
        }}
        .fg-brand-name {{ color:var(--fg-ink); font-family:'Manrope',sans-serif; font-size:1.16rem; font-weight:800; letter-spacing:-.045em; }}
        .fg-brand-tag {{ color:var(--fg-muted); font-size:.67rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; }}
        .fg-nav-line {{ margin: .5rem 0 1.8rem; height:1px; border:0; background:linear-gradient(90deg, var(--fg-line), transparent); }}

        /* Buttons: scope the light text override to button contents to prevent the primary-label bug. */
        div.stButton > button, div[data-testid="stFormSubmitButton"] > button, div[data-testid="stDownloadButton"] > button {{
            width:100% !important; min-height:2.7rem !important; border-radius:.8rem !important; padding:.54rem 1rem !important;
            border:1px solid var(--fg-line) !important; background:var(--fg-surface) !important; color:var(--fg-ink) !important;
            font-family:'DM Sans',sans-serif !important; font-size:.88rem !important; font-weight:700 !important;
            box-shadow:0 3px 8px rgba(25, 35, 65, .05) !important; transition:transform .18s ease, border-color .18s ease, background .18s ease, box-shadow .18s ease !important;
        }}
        /* Treat the complete painted button surface as the interactive control. */
        div.stButton, div[data-testid="stFormSubmitButton"], div[data-testid="stDownloadButton"] {{ width:100% !important; }}
        div.stButton > button, div[data-testid="stFormSubmitButton"] > button, div[data-testid="stDownloadButton"] > button {{ display:flex !important; align-items:center !important; justify-content:center !important; cursor:pointer !important; }}
        div.stButton > button > *, div[data-testid="stFormSubmitButton"] > button > *, div[data-testid="stDownloadButton"] > button > * {{ pointer-events:none !important; }}
        div.stButton > button *, div[data-testid="stFormSubmitButton"] > button *, div[data-testid="stDownloadButton"] > button * {{ color:inherit !important; }}
        div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover, div[data-testid="stDownloadButton"] > button:hover {{
            transform:translateY(-1px); border-color:var(--fg-input_line) !important; background:rgba(255, 255, 255, .92) !important; color:var(--fg-ink) !important; box-shadow:0 10px 22px rgba(0, 112, 117, .18) !important;
        }}
        /* Secondary / spark hover: the surface gets light, so labels must become dark. */
        button[data-testid="stBaseButton-secondary"]:hover, button[kind="secondary"]:hover {{
            background:rgba(255, 255, 255, .96) !important; color:#123239 !important;
        }}
        button[data-testid="stBaseButton-secondary"]:hover *, button[kind="secondary"]:hover * {{ color:#123239 !important; }}
        div.stButton > button[kind="primary"], div[data-testid="stFormSubmitButton"] > button[kind="primary"] {{
            background:linear-gradient(135deg, var(--fg-accent), #0A9DCB) !important; border-color:transparent !important; color:#FFFFFF !important; box-shadow:0 10px 22px rgba(0, 139, 146, .28) !important;
        }}
        div.stButton > button[kind="primary"]:hover, div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover, button[data-testid="stBaseButton-primaryFormSubmit"]:hover {{
            background:rgba(255, 255, 255, .96) !important; border-color:var(--fg-input_line) !important; color:#123239 !important; box-shadow:0 10px 22px rgba(0, 112, 117, .18) !important;
        }}
        div.stButton > button[kind="primary"]:hover *, div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover *, button[data-testid="stBaseButton-primary"]:hover *, button[data-testid="stBaseButton-primaryFormSubmit"]:hover * {{ color:#123239 !important; }}
        /* Disabled CTAs can still receive a browser hover state: force their label dark on the pale surface. */
        div.stButton > button:disabled, div.stButton > button:disabled:hover, div[data-testid="stFormSubmitButton"] > button:disabled, div[data-testid="stFormSubmitButton"] > button:disabled:hover, button[data-testid="stBaseButton-primary"]:disabled, button[data-testid="stBaseButton-primary"]:disabled:hover {{ background:var(--fg-surface_alt) !important; border-color:var(--fg-line) !important; color:var(--fg-ink) !important; opacity:.78 !important; transform:none !important; box-shadow:none !important; }}
        div.stButton > button:disabled *, div.stButton > button:disabled:hover *, div[data-testid="stFormSubmitButton"] > button:disabled *, div[data-testid="stFormSubmitButton"] > button:disabled:hover *, button[data-testid="stBaseButton-primary"]:disabled *, button[data-testid="stBaseButton-primary"]:disabled:hover * {{ color:var(--fg-ink) !important; }}

        /* Cards and information surfaces */
        .fg-card {{
            position:relative; min-height:12.6rem; overflow:hidden; background:var(--fg-surface) !important; border:1px solid var(--fg-line) !important;
            border-radius:1.15rem !important; padding:1.35rem 1.42rem !important; margin-bottom:1rem !important; box-shadow:0 6px 18px rgba(35, 48, 85, .05) !important;
            backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px); transition:transform .2s ease, box-shadow .2s ease, border-color .2s ease !important;
        }}
        .fg-card::before {{ content:''; position:absolute; width:7rem; height:7rem; right:-3.2rem; bottom:-3.2rem; border-radius:50%; background:var(--fg-accent_soft); }}
        .fg-card:hover {{ transform:translateY(-3px); border-color:var(--fg-accent) !important; box-shadow:var(--fg-shadow) !important; }}
        .fg-card-title {{ color:var(--fg-ink) !important; font-family:'Manrope',sans-serif; font-size:1.03rem; font-weight:800; letter-spacing:-.025em; }}
        .fg-card-copy {{ position:relative; z-index:1; color:var(--fg-muted) !important; font-size:.91rem; line-height:1.6; margin:1rem 0 0 !important; }}
        .model-badge {{ position:relative; z-index:1; background:var(--fg-blue_soft) !important; color:var(--fg-ink) !important; border:1px solid var(--fg-line) !important; padding:.28rem .58rem !important; border-radius:999px !important; font-size:.68rem !important; font-weight:800 !important; letter-spacing:.02em !important; white-space:nowrap; }}
        .hero-badge {{ display:inline-flex !important; align-items:center; gap:.4rem; background:var(--fg-accent_soft) !important; color:var(--fg-accent) !important; border:1px solid color-mix(in srgb, var(--fg-accent) 26%, transparent) !important; padding:.38rem .7rem !important; border-radius:999px !important; font-size:.7rem !important; font-weight:800 !important; margin-bottom:1rem !important; text-transform:uppercase !important; letter-spacing:.1em !important; }}
        .fg-trust-card {{ background:var(--fg-surface_alt); border:1px solid var(--fg-line); border-radius:1rem; padding:1.1rem 1.2rem; margin:1.3rem 0 1.15rem; backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px); }}
        .fg-trust-card strong {{ color:var(--fg-ink) !important; }}
        .fg-trust-card p {{ color:var(--fg-muted) !important; }}
        .fg-stat {{ background:var(--fg-surface); border:1px solid var(--fg-line); border-radius:.95rem; padding:.85rem 1rem; height:100%; backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px); }}
        .fg-stat-value {{ color:var(--fg-accent) !important; font-family:'Manrope',sans-serif; font-size:1.22rem; font-weight:800; }}
        .fg-stat-label {{ color:var(--fg-muted) !important; font-size:.75rem; font-weight:700; }}
        .fg-hero {{ position:relative; overflow:hidden; padding:1.2rem 0 1.4rem; }}
        .fg-hero::after {{ content:''; position:absolute; width:22rem; height:22rem; border-radius:50%; right:-14rem; top:-14rem; background:radial-gradient(circle, var(--fg-accent_soft), transparent 68%); pointer-events:none; }}
        .fg-hero-title {{ position:relative; z-index:1; max-width:52rem; margin:0 !important; color:var(--fg-ink) !important; font-family:'Manrope',sans-serif; font-size:clamp(2.25rem, 5vw, 4.1rem); font-weight:800; letter-spacing:-.065em; line-height:1.04; }}
        .fg-hero-title span {{ color:var(--fg-accent) !important; }}
        .fg-hero-copy {{ position:relative; z-index:1; max-width:42rem; margin:1.2rem 0 0 !important; color:var(--fg-muted) !important; font-size:1.1rem; line-height:1.65; }}
        .fg-section-kicker {{ color:var(--fg-accent) !important; font-size:.74rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.3rem; }}
        .fg-step {{ background:var(--fg-surface); border:1px solid var(--fg-line); border-radius:.85rem; padding:.65rem .45rem; text-align:center; }}
        .fg-step-tag {{ color:var(--fg-muted) !important; font-size:.66rem; font-weight:800; letter-spacing:.08em; }}
        .fg-step-label {{ color:var(--fg-muted) !important; font-size:.8rem; font-weight:800; }}
        .fg-step.is-done {{ background:var(--fg-blue_soft); border-color:transparent; }}
        .fg-step.is-done .fg-step-tag {{ color:#129681 !important; }}
        .fg-step.is-done .fg-step-label {{ color:var(--fg-ink) !important; }}
        .fg-step.is-active {{ background:linear-gradient(135deg, var(--fg-accent), #0A9DCB); border-color:transparent; box-shadow:0 9px 18px rgba(0,139,146,.25); }}
        .fg-step.is-active .fg-step-tag {{ color:rgba(255,255,255,.7) !important; }}
        .fg-step.is-active .fg-step-label {{ color:#fff !important; }}


        /* Form controls */
        [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] > div {{
            background:var(--fg-surface) !important; color:var(--fg-ink) !important; border:1.5px solid var(--fg-input_line) !important; border-radius:.78rem !important; box-shadow:inset 0 1px 0 rgba(255,255,255,.22), 0 2px 6px rgba(0,55,60,.04) !important;
        }}
        [data-baseweb="base-input"] {{ background:transparent !important; }}
        [data-testid="stTextInput"] input::placeholder, [data-testid="stTextArea"] textarea::placeholder {{ color:var(--fg-muted) !important; opacity:.74 !important; }}
        [data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus, [data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"] > div:focus-within {{ border-color:var(--fg-accent) !important; box-shadow:0 0 0 3px var(--fg-accent_soft), 0 7px 18px rgba(0,128,131,.12) !important; }}
        [data-testid="stTextInput"] label, [data-testid="stTextArea"] label, [data-testid="stSelectbox"] label, [data-testid="stMultiSelect"] label, [data-testid="stNumberInput"] label, [data-testid="stCheckbox"] label {{ color:var(--fg-ink) !important; font-weight:700 !important; }}
        [data-baseweb="select"] * {{ color:var(--fg-ink) !important; }}
        [data-baseweb="tag"] {{ background:var(--fg-accent_soft) !important; border-radius:999px !important; }}
        [data-baseweb="tag"] * {{ color:var(--fg-accent) !important; }}
        [data-testid="stForm"] {{ background:var(--fg-surface); border:1px solid var(--fg-line); border-radius:1.15rem; padding:1.4rem 1.5rem 1.25rem; box-shadow:var(--fg-shadow); backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px); }}
        [data-testid="stExpander"] {{ background:var(--fg-surface_alt); border:1px solid var(--fg-line); border-radius:.85rem; backdrop-filter:blur(14px); }}
        [data-testid="stAlert"] {{ border-radius:.85rem !important; backdrop-filter:blur(14px); }}
        [data-testid="stMetric"] {{ background:var(--fg-surface); border:1px solid var(--fg-line); border-radius:.9rem; padding:1rem; backdrop-filter:blur(16px); }}

        /* Legacy report snippets use inline neutral colours. Map those neutrals to the active theme. */
        [data-testid="stMarkdownContainer"] [style*="background:#FFFFFF"], [data-testid="stMarkdownContainer"] [style*="background: #FFFFFF"] {{ background:var(--fg-surface) !important; }}
        [data-testid="stMarkdownContainer"] [style*="background:#F8FAFC"], [data-testid="stMarkdownContainer"] [style*="background: #F8FAFC"], [data-testid="stMarkdownContainer"] [style*="background:#F1F5F9"] {{ background:var(--fg-surface_alt) !important; }}
        [data-testid="stMarkdownContainer"] [style*="border:1px solid #E2E8F0"], [data-testid="stMarkdownContainer"] [style*="border: 1px solid #E2E8F0"], [data-testid="stMarkdownContainer"] [style*="border:1px solid #CBD5E1"] {{ border-color:var(--fg-line) !important; }}
        [data-testid="stMarkdownContainer"] [style*="color:#0F172A"], [data-testid="stMarkdownContainer"] [style*="color: #0F172A"], [data-testid="stMarkdownContainer"] [style*="color:#1E293B"], [data-testid="stMarkdownContainer"] [style*="color:#334155"] {{ color:var(--fg-ink) !important; }}
        [data-testid="stMarkdownContainer"] [style*="color:#475569"], [data-testid="stMarkdownContainer"] [style*="color:#64748B"], [data-testid="stMarkdownContainer"] [style*="color:#94A3B8"] {{ color:var(--fg-muted) !important; }}

        /* Tabs, progress, sidebar */
        [data-baseweb="tab-list"] {{ gap:.4rem; padding:.35rem; border:1px solid var(--fg-line); border-radius:1rem; background:var(--fg-surface); box-shadow:0 5px 14px rgba(0,83,88,.06); }}
        [data-baseweb="tab-list"] [data-baseweb="tab"] {{ flex:1 1 0; min-height:2.8rem; justify-content:center; border-radius:.72rem; color:var(--fg-muted) !important; font-size:.88rem; font-weight:800 !important; transition:background .18s ease, color .18s ease, box-shadow .18s ease; }}
        [data-baseweb="tab-list"] [data-baseweb="tab"]::after {{ display:none !important; }}
        [data-baseweb="tab-list"] [data-baseweb="tab"][aria-selected="true"] {{ background:linear-gradient(135deg, var(--fg-accent), #0A9DCB) !important; color:#FFFFFF !important; box-shadow:0 7px 16px rgba(0,139,146,.24); }}
        [data-baseweb="tab-list"] [data-baseweb="tab"][aria-selected="true"] * {{ color:#FFFFFF !important; }}
        [data-baseweb="tab-list"] [data-baseweb="tab"]:hover:not([aria-selected="true"]) {{ background:var(--fg-accent_soft); color:var(--fg-ink) !important; }}
        [data-testid="stProgress"] > div > div {{ background:linear-gradient(90deg, var(--fg-accent), #0A9DCB) !important; }}
        section[data-testid="stSidebar"] {{ background:linear-gradient(180deg, var(--fg-surface), var(--fg-surface_alt)) !important; border-right:1px solid var(--fg-line) !important; box-shadow:12px 0 36px rgba(0,93,99,.08); backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px); }}
        section[data-testid="stSidebar"] .block-container {{ padding-top:2rem !important; }}
        section[data-testid="stSidebar"]::before {{ content:''; position:absolute; inset:0 auto 0 0; width:4px; background:linear-gradient(180deg, var(--fg-accent), #0A9DCB, transparent 72%); }}
        .fg-sidebar-brand {{ display:flex; align-items:center; gap:.68rem; padding:.85rem .8rem; margin:0 0 1.45rem; background:var(--fg-surface_alt); border:1px solid var(--fg-line); border-radius:1rem; }}
        .fg-sidebar-mark {{ width:2rem; height:2rem; display:grid; place-items:center; background:linear-gradient(135deg, var(--fg-accent), #0A9DCB); color:#fff; border-radius:.7rem; font-weight:800; box-shadow:0 7px 16px rgba(0,139,146,.25); }}
        .fg-sidebar-title {{ color:var(--fg-ink) !important; font-family:'Manrope',sans-serif; font-size:.88rem; font-weight:800; }}
        .fg-sidebar-subtitle, .fg-sidebar-label {{ color:var(--fg-muted) !important; font-size:.65rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }}
        section[data-testid="stSidebar"] [data-testid="stButton"] > button {{ justify-content:flex-start !important; }}
        /* Make every pixel of the dark-mode control (switch and label) toggle the theme. */
        div.stElementContainer.st-key-theme_toggle, div.stElementContainer.st-key-theme_toggle [data-testid="stCheckbox"], div.stElementContainer.st-key-theme_toggle label[data-baseweb="checkbox"] {{ width:100% !important; box-sizing:border-box !important; }}
        /* Streamlit gives checkbox widgets extra top spacing; compensate so it shares the button baseline. */
        div.stElementContainer.st-key-theme_toggle {{ transform:translateY(-.45rem); }}
        div.stElementContainer.st-key-theme_toggle label[data-baseweb="checkbox"] {{ min-height:2.7rem !important; padding:.42rem .7rem !important; display:flex !important; align-items:center !important; gap:.55rem !important; border:1px solid transparent; border-radius:.8rem; cursor:pointer !important; user-select:none; }}
        /* Let the label receive every click, including the text and the padded right-hand area. */
        div.stElementContainer.st-key-theme_toggle label[data-baseweb="checkbox"] > * {{ pointer-events:none !important; }}
        div.stElementContainer.st-key-theme_toggle label[data-baseweb="checkbox"]:hover {{ background:rgba(255,255,255,.72) !important; border-color:var(--fg-input_line) !important; color:#123239 !important; }}
        div.stElementContainer.st-key-theme_toggle label[data-baseweb="checkbox"]:hover * {{ color:#123239 !important; }}
        [data-testid="stToggle"] label, div.stElementContainer.st-key-theme_toggle label {{ color:var(--fg-muted) !important; font-size:.78rem !important; font-weight:700 !important; white-space:nowrap; }}
        /* A visible collapsed-menu tab makes navigation discoverable before the sidebar is opened. */
        [data-testid="stSidebarCollapsedControl"] {{ position:fixed !important; top:6.25rem !important; left:0 !important; z-index:999 !important; min-width:11.9rem !important; min-height:3rem !important; padding:.38rem .7rem !important; display:flex !important; align-items:center !important; gap:.42rem !important; background:var(--fg-surface_alt) !important; border:1px solid var(--fg-input_line) !important; border-left:0 !important; color:var(--fg-ink) !important; border-radius:0 .9rem .9rem 0 !important; box-shadow:0 10px 26px rgba(0,83,88,.18) !important; backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px); }}
        [data-testid="stSidebarCollapsedControl"] [data-testid="stLogoSpacer"] {{ display:none !important; }}
        /* The Streamlit arrow is the real control; stretch it over the entire visible tab. */
        [data-testid="stSidebarCollapsedControl"] > div:not([data-testid="stLogoSpacer"]) {{ position:absolute !important; inset:0 !important; z-index:2 !important; }}
        [data-testid="stSidebarCollapsedControl"] button {{ width:100% !important; height:100% !important; padding:0 !important; border-radius:.8rem !important; background:transparent !important; color:var(--fg-accent) !important; cursor:pointer !important; }}
        [data-testid="stSidebarCollapsedControl"] button svg {{ position:absolute !important; left:.8rem !important; top:50% !important; transform:translateY(-50%) !important; width:1.05rem !important; height:1.05rem !important; }}
        [data-testid="stSidebarCollapsedControl"]::after {{ content:'Open navigation'; position:absolute; left:2.25rem; top:50%; z-index:1; transform:translateY(-50%); color:var(--fg-ink) !important; font-family:'DM Sans',sans-serif; font-size:.78rem; font-weight:800; letter-spacing:.01em; pointer-events:none; }}
        /* The navigation tab uses a pale spark hover, therefore both its icon and label stay dark. */
        [data-testid="stSidebarCollapsedControl"]:hover {{ background:rgba(255,255,255,.96) !important; border-color:var(--fg-input_line) !important; color:#123239 !important; }}
        [data-testid="stSidebarCollapsedControl"]:hover button {{ background:var(--fg-accent_soft) !important; color:#123239 !important; }}
        [data-testid="stSidebarCollapsedControl"]:hover::after {{ color:#123239 !important; }}
        [data-testid="stSidebarCollapseButton"] button {{ border:1px solid var(--fg-line) !important; border-radius:.65rem !important; background:var(--fg-surface_alt) !important; color:var(--fg-ink) !important; }}
        hr {{ border-color:var(--fg-line) !important; }}
        @media (max-width: 720px) {{ .block-container {{ padding:1rem 1rem 3rem !important; }} .fg-card {{ min-height:auto; }} }}
    </style><div class="fg-bottom-tone" aria-hidden="true"></div>
    """, unsafe_allow_html=True)


inject_global_styles(st.session_state["ui_theme"])


def update_theme() -> None:
    st.session_state["ui_theme"] = "dark" if st.session_state["theme_toggle"] else "light"


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

# ── Global Top Navigation Header ──────────────────────────────────────────────
with st.container():
    h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns([2.8, 1.1, 1.4, 1.0, 1.5])
    with h_col1:
        st.markdown(
            """
            <div class="fg-brand">
                <div class="fg-brand-mark" aria-hidden="true">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2.5 19 5.3v5.3c0 4.5-2.9 8.6-7 10.2-4.1-1.6-7-5.7-7-10.2V5.3L12 2.5Z" fill="currentColor" fill-opacity=".22" stroke="currentColor" stroke-width="1.6"/>
                        <path d="m8.5 12 2.15 2.15L15.8 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div>
                    <div class="fg-brand-name">FounderGuard AI</div>
                    <div class="fg-brand-tag">Founder intelligence</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with h_col2:
        if st.button("Home", key="global_top_nav_home", use_container_width=True):
            start_over()
    with h_col3:
        if st.button("Model Docs", key="global_top_nav_about", use_container_width=True):
            goto("about")
    with h_col4:
        st.toggle("Dark", key="theme_toggle", on_change=update_theme)
    with h_col5:
        curr_page = st.session_state.get("page", "landing")
        if curr_page == "form":
            step_num = st.session_state.get("step", 1)
            st.markdown(
                f"<div style='text-align:right;padding-top:6px;font-size:0.85rem;color:#475569;font-weight:600;'>Step {step_num} of 5</div>",
                unsafe_allow_html=True,
            )
        elif curr_page == "landing":
            if st.button("Start Evaluation", key="global_top_nav_start", type="primary", use_container_width=True):
                goto("form", step=1)
        else:
            if st.button("New Evaluation", key="global_top_nav_new", type="primary", use_container_width=True):
                start_over()

st.markdown("<hr class='fg-nav-line'>", unsafe_allow_html=True)

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
