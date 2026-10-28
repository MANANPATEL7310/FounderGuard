"""Five-step form: collects all submission fields."""
from __future__ import annotations
import streamlit as st
from frontend.ui_helpers import word_meter

STEPS = {
    1: "Your Idea",
    2: "Market & Business",
    3: "Stage & Money",
    4: "Your Team",
    5: "Evidence (optional)",
}


def _step_header(current: int):
    cols = st.columns(len(STEPS))
    for i, (num, label) in enumerate(STEPS.items()):
        icon = "✅" if num < current else ("→" if num == current else "○")
        cols[i].markdown(
            f"<div style='text-align:center;font-size:13px'>{icon}<br><b>{label}</b></div>",
            unsafe_allow_html=True,
        )
    st.markdown("---")


def render(goto, opts: dict, start_over):
    step = st.session_state["step"]

    # Sidebar navigation
    with st.sidebar:
        st.markdown("### Navigation")
        if st.button("⬅ Back to Landing"):
            start_over()
        st.markdown("---")
        st.info("💡 Nothing is saved until you submit on the Review page.")
        if st.button("🔄 Start Over"):
            start_over()
        st.markdown("---")
        if st.button("ℹ About the Models"):
            goto("about")

    st.title("🚀 Startup Evaluation Form")
    _step_header(step)

    if step == 1:
        _step1(goto, opts)
    elif step == 2:
        _step2(goto, opts)
    elif step == 3:
        _step3(goto, opts)
    elif step == 4:
        _step4(goto, opts)
    elif step == 5:
        _step5(goto, opts)


# ── Step 1: Your Idea ─────────────────────────────────────────────────────────
def _step1(goto, opts):
    st.subheader("Step 1 — Your Idea")
    st.caption("The idea description is the most important field. Models C and D read it directly.")

    with st.form("step1_form"):
        idea = st.text_area(
            "Idea Description *",
            value=st.session_state["f_idea"],
            height=180,
            max_chars=4000,
            help="Describe your startup idea in 200–4,000 characters. The more specific, the better.",
            placeholder="e.g. An AI-powered platform that automates invoice reconciliation for mid-market freight brokers, reducing manual work by 80%...",
        )

        # Live word meter (shown below textarea)
        if idea:
            icon, msg = word_meter(idea)
            st.caption(f"{icon} {len(idea.split())} words — {msg}")

        problem = st.text_area(
            "Problem being solved (optional)",
            value=st.session_state["f_problem"],
            max_chars=1000,
            help="What pain point does this solve? Feeds Model C's problem analysis.",
            placeholder="e.g. Freight brokers manually match 200+ invoices per day across 5 different carrier portals...",
        )
        customer = st.text_area(
            "Target customer (optional)",
            value=st.session_state["f_customer"],
            max_chars=500,
            help="Who will pay for this? Feeds Model C's customer analysis.",
            placeholder="e.g. Mid-market US freight brokers with 10–100 employees...",
        )

        # Model A optional enrichment
        with st.expander("📅 Model A date inputs (optional — improves outcome prediction)"):
            st.caption("Model A requires founding and funding dates to run. Without them it is marked Not Applicable.")
            col1, col2, col3 = st.columns(3)
            founded_at = col1.text_input(
                "Founded date (YYYY-MM-DD)",
                value=st.session_state["f_founded_at"],
                placeholder="2021-03-15",
            )
            first_funding = col2.text_input(
                "First funding date (YYYY-MM-DD)",
                value=st.session_state["f_first_funding_at"],
                placeholder="2021-09-01",
            )
            last_funding = col3.text_input(
                "Last funding date (YYYY-MM-DD)",
                value=st.session_state["f_last_funding_at"],
                placeholder="2022-06-01",
            )
            homepage = st.text_input(
                "Homepage URL (optional)",
                value=st.session_state["f_homepage_url"],
                placeholder="https://yourstartup.com",
            )
            col4, col5 = st.columns(2)
            city = col4.text_input("City", value=st.session_state["f_city"], placeholder="San Francisco")
            region = col5.text_input("Region / Metro", value=st.session_state["f_region"], placeholder="SF Bay Area")

        submitted = st.form_submit_button("Next: Market & Business →", type="primary")

    if submitted:
        if not idea or len(idea.strip()) < 20:
            st.error("Idea description must be at least 20 characters.")
            return
        st.session_state["f_idea"] = idea
        st.session_state["f_problem"] = problem
        st.session_state["f_customer"] = customer
        st.session_state["f_founded_at"] = founded_at
        st.session_state["f_first_funding_at"] = first_funding
        st.session_state["f_last_funding_at"] = last_funding
        st.session_state["f_homepage_url"] = homepage
        st.session_state["f_city"] = city
        st.session_state["f_region"] = region
        goto("form", step=2)


# ── Step 2: Market & Business ─────────────────────────────────────────────────
def _step2(goto, opts):
    st.subheader("Step 2 — Market & Business")
    st.caption("These fields determine how your startup is classified by the models.")

    industries = opts.get("industries", ["Other"])
    countries = opts.get("countries", ["USA"])
    us_states = opts.get("us_states", [])
    biz_models = opts.get("business_models", [])

    def _safe_idx(lst, val, default=0):
        try:
            return lst.index(val) if val in lst else default
        except Exception:
            return default

    with st.form("step2_form"):
        industry = st.selectbox(
            "Industry / Sector *",
            options=industries,
            index=_safe_idx(industries, st.session_state["f_industry"]),
            help="Used to map to Model B's category and Model C's sector.",
        )
        country = st.selectbox(
            "Country *",
            options=countries,
            index=_safe_idx(countries, st.session_state["f_country"]),
            help="Non-US startups run Model B with a location warning. Model A handles non-US gracefully.",
        )

        # US state — shown only for USA
        state = ""
        if country == "USA":
            state_opts = [""] + us_states
            state = st.selectbox(
                "US State *",
                options=state_opts,
                index=_safe_idx(state_opts, st.session_state["f_state"]),
                help="Required for US startups. Unlisted states become OTHER in Model B.",
            )

        target_market = st.selectbox(
            "Target market *",
            options=["local", "national", "regional", "global"],
            index=["local", "national", "regional", "global"].index(
                st.session_state["f_target_market"]
                if st.session_state["f_target_market"] in ["local", "national", "regional", "global"]
                else "global"
            ),
        )

        biz_model_sel = st.multiselect(
            "Business model(s) *",
            options=biz_models,
            default=[b for b in st.session_state["f_business_model"] if b in biz_models],
            help="Select all that apply. Feeds Model C's business model analysis.",
        )

        col_back, col_next = st.columns([1, 3])
        back = col_back.form_submit_button("← Back")
        submitted = col_next.form_submit_button("Next: Stage & Money →", type="primary")

    if back:
        goto("form", step=1)
    if submitted:
        errors = []
        if not industry:
            errors.append("Select an industry.")
        if not country:
            errors.append("Select a country.")
        if country == "USA" and not state:
            errors.append("Select a US state.")
        if not biz_model_sel:
            errors.append("Select at least one business model.")
        if errors:
            for e in errors:
                st.error(e)
            return
        st.session_state["f_industry"] = industry
        st.session_state["f_country"] = country
        st.session_state["f_state"] = state
        st.session_state["f_target_market"] = target_market
        st.session_state["f_business_model"] = biz_model_sel
        goto("form", step=3)


# ── Step 3: Stage & Money ─────────────────────────────────────────────────────
def _step3(goto, opts):
    st.subheader("Step 3 — Stage & Money")
    st.caption(
        "Only **Funding raised** (money from investors) feeds Model B. "
        "Budget is what you can spend — it feeds the LLM context only."
    )

    currencies = opts.get("currencies", ["USD", "EUR", "GBP", "INR", "CAD"])
    stages = opts.get("stages", ["idea", "validation", "MVP", "launched", "growing"])
    inv_types = opts.get("investor_types", ["venture capital", "angel", "none"])
    round_opts = opts.get("funding_rounds_options", ["Round A", "Round B", "Round C", "Round D", "none"])

    with st.form("step3_form"):
        stage = st.selectbox(
            "Current stage *",
            options=stages,
            index=stages.index(st.session_state["f_stage"]) if st.session_state["f_stage"] in stages else 0,
            help="'idea' stage means no funding yet — Model B will be not applicable.",
        )

        st.markdown("#### 💰 Funding raised from investors")
        st.caption("This is money you have already received from investors — not your budget.")
        col1, col2 = st.columns([3, 1])
        funding_raised = col1.number_input(
            "Amount raised *",
            min_value=0.0,
            value=float(st.session_state["f_funding_raised"]),
            step=10000.0,
            help="Enter 0 if you have not raised any external investment.",
        )
        currency = col2.selectbox(
            "Currency",
            options=currencies,
            index=currencies.index(st.session_state["f_currency"]) if st.session_state["f_currency"] in currencies else 0,
        )

        # Conditional fields — only when funding > 0
        funding_rounds = 0
        investor_types = []
        rounds_reached = []
        if funding_raised > 0:
            funding_rounds = st.number_input(
                "Number of funding rounds *",
                min_value=1,
                max_value=20,
                value=max(1, int(st.session_state["f_funding_rounds"])),
                help="How many formal investment rounds have you closed?",
            )
            investor_types = st.multiselect(
                "Investor types *",
                options=inv_types,
                default=[t for t in st.session_state["f_investor_types"] if t in inv_types],
                help="Select all that have invested. Feeds has_VC and has_angel in Model B.",
            )
            rounds_reached = st.multiselect(
                "Milestone rounds reached (optional)",
                options=round_opts,
                default=[r for r in st.session_state["f_rounds_reached"] if r in round_opts],
                help="E.g. 'Round A' if you completed a Series A.",
            )
        else:
            st.info("ℹ Model A and Model B will be **Not Applicable** (no funding or rounds). Models C and D will still run.")

        st.markdown("#### 💼 Budget available (optional)")
        st.caption("Your own operational budget — not investment. This is for the recommendation context only, not modelled.")
        col3, col4 = st.columns([3, 1])
        budget = col3.number_input(
            "Budget",
            min_value=0.0,
            value=float(st.session_state["f_budget"]),
            step=1000.0,
        )

        col_back, col_next = st.columns([1, 3])
        back = col_back.form_submit_button("← Back")
        submitted = col_next.form_submit_button("Next: Your Team →", type="primary")

    if back:
        goto("form", step=2)
    if submitted:
        st.session_state["f_stage"] = stage
        st.session_state["f_funding_raised"] = funding_raised
        st.session_state["f_currency"] = currency
        st.session_state["f_budget"] = budget
        st.session_state["f_funding_rounds"] = int(funding_rounds) if funding_raised > 0 else 0
        st.session_state["f_investor_types"] = investor_types
        st.session_state["f_rounds_reached"] = rounds_reached
        goto("form", step=4)


# ── Step 4: Your Team ─────────────────────────────────────────────────────────
def _step4(goto, opts):
    st.subheader("Step 4 — Your Team")
    st.caption("Team information feeds Model D's narrative text and the recommendations engine.")

    skills = opts.get("team_skills", ["engineering", "product", "design", "sales and marketing", "operations", "finance", "domain expertise", "other"])
    exp_levels = opts.get("founder_experience", ["first-time", "prior startup", "prior exit", "domain veteran"])

    with st.form("step4_form"):
        team_size = st.number_input(
            "Team size *",
            min_value=1,
            max_value=500,
            value=int(st.session_state["f_team_size"]),
            help="Full-time and core part-time members.",
        )
        team_skills = st.multiselect(
            "Core skills present in team *",
            options=skills,
            default=[s for s in st.session_state["f_team_skills"] if s in skills],
            help="Select all that apply.",
        )
        exp_idx = exp_levels.index(st.session_state["f_founder_experience"]) if st.session_state["f_founder_experience"] in exp_levels else 0
        founder_exp = st.selectbox(
            "Founder experience *",
            options=exp_levels,
            index=exp_idx,
        )

        col_back, col_next = st.columns([1, 3])
        back = col_back.form_submit_button("← Back")
        submitted = col_next.form_submit_button("Next: Evidence →", type="primary")

    if back:
        goto("form", step=3)
    if submitted:
        errors = []
        if not team_skills:
            errors.append("Select at least one skill.")
        if errors:
            for e in errors:
                st.error(e)
            return
        st.session_state["f_team_size"] = int(team_size)
        st.session_state["f_team_skills"] = team_skills
        st.session_state["f_founder_experience"] = founder_exp
        goto("form", step=5)


# ── Step 5: Evidence (optional) ───────────────────────────────────────────────
def _step5(goto, opts):
    st.subheader("Step 5 — Evidence (all optional)")
    st.caption(
        "These fields feed Model C's aspect analysis. Blank means 'not provided' — never a weakness. "
        "A blank is never shown negatively in the report."
    )

    with st.form("step5_form"):
        validation = st.text_area(
            "Existing validation",
            value=st.session_state["f_validation"],
            max_chars=1000,
            help="Customer interviews, pilot users, letters of intent, surveys, waitlist.",
            placeholder="e.g. Ran 40 discovery interviews with freight brokers, 8 signed LOIs, 3 paying pilots at $500/mo...",
        )
        competitors = st.text_area(
            "Known competitors or alternatives",
            value=st.session_state["f_competitors"],
            max_chars=1000,
            help="Feeds Model C's competitive landscape analysis.",
            placeholder="e.g. Flexport, Convoy, manual spreadsheet workflows...",
        )
        traction = st.text_area(
            "Traction",
            value=st.session_state["f_traction"],
            max_chars=1000,
            help="Paying customers, active users, MRR, retention — anything measurable.",
            placeholder="e.g. $4,500 MRR, 12 active customers, 82% month-2 retention...",
        )

        col_back, col_next = st.columns([1, 3])
        back = col_back.form_submit_button("← Back")
        submitted = col_next.form_submit_button("Review My Submission →", type="primary")

    if back:
        goto("form", step=4)
    if submitted:
        st.session_state["f_validation"] = validation
        st.session_state["f_competitors"] = competitors
        st.session_state["f_traction"] = traction
        goto("review")

