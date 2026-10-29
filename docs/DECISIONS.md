# Project Decision Log

This file records key architectural, engineering, and product decisions made during development.

---

## Decision 001: Operational Working Rules & Constraints

- **Date:** 2026-10-28
- **Status:** Accepted
- **Context:** Guidelines set by the project owner for agent collaboration and code development.
- **Rules Established:**
  1. **Strict step-by-step progress:** Proceed one step at a time. Never begin the next step until the "done when" criteria of the current step pass and are verified.
  2. **Confirmation & Decision Tracking:** Whenever an item is marked "confirm", ambiguous, or unclear, ask the user directly before proceeding. Record every decision in `docs/DECISIONS.md`.
  3. **Preserve Model Artifacts & Code:** Never edit the models' `.py` inference/feature files (`startup_features.py`, `model_b_inference.py`, `model_c_inference.py`, `model_d_inference.py`) or attempt to retrain models. If model changes are needed, they must be done in the training notebooks.
  4. **No Auth/User Accounts:** Do not add login, sign-up, or user account systems.
  5. **Regression Testing:** After each step, run the entire test suite, not just tests added in the current step.


---

## Decision 002: Git Branching and Commit-Based Workflow

- **Date:** 2026-10-28
- **Status:** Accepted
- **Context:** Project owner requested a branch- and commit-based workflow for code tracking.
- **Workflow Established:**
  1. **Step-Specific Feature Branches:** Each build step will operate on its own branch branched from `main` (e.g. `feat/step-0-workspace-smoke-test`, `feat/step-1-backend-core`, etc.).
  2. **Scoped Commits:** Code within each step will be committed with descriptive conventional commit messages.
  3. **Verification Before Merge:** The entire test suite must pass before a branch is considered ready.
  4. **Step Completion:** Upon passing the "done when" criteria, the step's branch can be merged to `main` (or reviewed by user) before starting the next step.

---

## Decision 003: Model A Architecture and Input Contracts

- **Date:** 2026-10-28
- **Status:** Accepted
- **Context:** Empirically verified Model A characteristics in Step 0.
- **Findings & Decisions:**
  1. **Bundle Structure:** `startup_outcome_classifier.pkl` is a dictionary bundle containing `['model', 'model_name', 'raw_columns', 'feature_columns']`. The model is `catboost.core.CatBoostClassifier`.
  2. **Class Meaning:** `classes_ = [0, 1]` where 0 represents Closed/Failure and 1 represents Operating/Active/Success (Acquired/IPO/Operating).
  3. **Input Features:** 11 raw columns mapped to 17 engineered features (12 numeric + 5 categorical).
  4. **Pre-funding & Non-US Behavior:**
     - Pre-funding ideas run without crashing (CatBoost native NaN support + `funding_missing=1.0`), yielding 52.2% Closed / 47.8% Operating.
     - Non-US startups run without crashing (location imputed to `'missing'`, country retained).

---

## Decision 004: Model A Applicability, Required Date Rules & Year-Shift Sensitivity

- **Date:** 2026-10-28
- **Status:** Accepted
- **Context:** Project owner confirmed requirements for Model A execution in Step 1.
- **Decisions Established:**
  1. **Pre-funding Applicability (Option A):** Model A is strictly **Not Applicable** when `funding_total_usd == 0` or `funding_rounds == 0`.
  2. **Field Requirements for Model A:**
     - `homepage_url`, `city`, and `region` are optional.
     - `founded_at`, `first_funding_at`, and `last_funding_at` are strictly required for Model A to run. If any of these three dates is missing, Model A is marked **Not Applicable** with reason: `"dates missing"`. No date imputation is performed.
  3. **Temporal Boundary & Trust Panel Warning:**
     - Training data analysis of `big_startup_secsees_dataset.csv` in `Material/notebooks/ml-model-a.ipynb` confirmed that the 99th percentile and effective upper bound of training years is **2015** (December 2015).
     - Startups with `founded_year`, `first_funding_year`, or `last_funding_year` > 2015 are passed through to the model, and a prominent warning is attached to the Trust Panel notifying the user of temporal distribution drift.
  4. **Year-Shift Sensitivity Test Results (2012 vs 2024):**
     - Identical startup profile evaluated (\$2.0M funding, 2 rounds, CA/SF Bay Area, Software/AI):
       - **2012 Cohort (In-Distribution):** `P(Closed) = 0.2980`, `P(Operating/Success) = 0.7020`
       - **2024 Cohort (Temporal Shift):** `P(Closed) = 0.2174`, `P(Operating/Success) = 0.7826`
       - **Observed Drift:** $\Delta P(\text{Operating/Success}) = +0.0806$ (+8.06%). Later years artificially lean slightly toward active/success due to right-censoring in Crunchbase data (companies founded more recently had fewer calendar years to fail before the snapshot date).

---

## Decision 005: Streamlit Frontend Architecture and Flow

- **Date:** 2026-10-28
- **Status:** Accepted
- **Context:** Step 2 Streamlit implementation (Planning file 03, plus 01 section 1.1, 02 sections 2.3 and 2.4).
- **Architecture & Rules Established:**
  1. **Page Flow State Machine:** Controlled via `st.session_state["page"]` and `st.session_state["step"]`:
     `landing` -> `form` (steps 1 to 5) -> `review` (calls `/validate`) -> `processing` (polls status) -> `report` (renders full 8-section report) with an omnipresent `about` page.
  2. **Zero Model Coupling in Frontend:** The frontend runs no models, maps no categories, and performs no currency conversion. All dropdown lists and constraints are fetched from `/v1/meta/options`.
  3. **Word Meter:** Real-time character/word tracker on idea description with color-coded guidance (red under 40 words, amber 40-80, green 80+).
  4. **Conditional Inputs:**
     - US State is only shown if Country is USA.
     - Funding rounds, investor types, and rounds reached are shown only if funding raised > 0.
     - Founding and funding dates are optional in the form, but their absence cleanly triggers Model A's Not Applicable card.
  5. **Review Page Verification:** Calls `POST /v1/evaluations/validate` to show the user which models will run, which will be skipped and why, the exact USD conversion, and warnings before submission.
  6. **Report Visualizations:**
     - Interpretation banner with distinct iconography and template explanation (never color alone).
     - Model A outcome probabilities bar chart and target definition.
     - Model B failure risk gauge/card with relative risk score (0-100), level badge, and meaning text.
     - Model C 8 aspect dimension cards with status badges and quoted evidence sentences.
     - Model D 8 failure category bars with evidence sentences, historical similarity, and out-of-distribution warning banner if flagged.
     - Trust Panel with provenance tracking (provided vs unstated fields), currency conversion rates, and limitations.
     - Recommendations tab showing "Coming Soon" placeholder for Step 3/4.
     - Privacy controls: "Delete My Data" invoking `DELETE /v1/evaluations/{id}`.


---

## Decision 006: Recommendation Engine Architecture, Priority Rules & Playbook Fallback

- **Date:** 2026-10-28
- **Status:** Accepted
- **Context:** Step 3 implementation of recommendations without an LLM (Planning 05 sections 5.4, 5.5, 5.8, 5.10, and Planning 04 section 4.6).
- **Architecture & Rules Established:**
  1. **Shared Theme Taxonomy:** 11 shared themes mapping across all 4 models:
     - 8 Model D categories: `market_demand`, `funding_cashflow`, `competition_differentiation`, `unit_economics_pricing`, `acquisition_retention`, `team_operations`, `weak_business_model`, `product_market_fit`.
     - 3 extra operational themes: `idea_clarity`, `validation_evidence`, `execution_hurdles`.
  2. **Deterministic Priority Rules:**
     - **High Priority:**
       - Supported by 2 or more distinct models (e.g., Model D prediction + Model C aspect gap).
       - Model D predicts theme with acceptable label quality (`predicted == True`).
       - Matches a Model B risk-raising factor while Model B overall risk is High or Very High.
     - **Medium Priority:**
       - Single model moderate signal (e.g., Model D prob >= 0.40, Model C partial/risk signal, or Model B moderate factor).
     - **Low Priority:**
       - Weak single signals or uncorroborated "not stated" gaps in optional fields.
  3. **Out-of-Distribution (OOD) Capping:**
     - When Model D OOD is flagged (`ood.flagged == True`), any issue supported solely by Model D is strictly capped at **Medium** priority. Multi-model corroborated issues retain High.
  4. **Strict "Not Stated" Framing:**
     - Unstated fields are never described as confirmed problems or faults; they are framed as validation/clarification requests.
  5. **Curated Playbook Knowledge Base:**
     - 13 curated advice chunks stored in `playbook/playbook_data.json` covering: customer discovery interviews, landing-page smoke tests, concierge MVPs, competitor differentiation mapping, pricing sensitivity experiments, unit economics audits, channel testing, retention cohorts, runway planning, skills gap audits, business model canvas, idea clarity, and pivot criteria.
     - Playbook matching filters by both `theme` and operational `stage` (e.g., pre-funding ideas receive discovery advice, not fundraising plans).
  6. **Recommendation Structure Parity (Section 5.8):**
     - Every recommendation item strictly adheres to the 7 plan fields: `identified_problem_or_risk`, `why_it_matters_for_this_startup`, `specific_action`, `priority` (must equal assigned priority), `implementation_steps`, `expected_benefit`, `validation_method`, plus `evidence_refs`, `playbook_refs`, and `assumptions`. No success guarantees are made.
  7. **Fallback & LLM-Off Mode:**
     - Served deterministically at `GET /v1/evaluations/{id}/recommendations` with `generation_method: "template_playbook"` and `is_fallback: True`. Shows a dedicated playbook banner in the UI.

---

## Decision 007: Open-Source LLM Integration, Grounding, Validation, Repair & Caching

- **Date:** 2026-10-29
- **Status:** Accepted
- **Context:** Step 4 implementation of recommendations with an open-source LLM (Planning 05 sections 5.1 to 5.3, 5.6 to 5.9, 5.11, and 5.12).
- **Architecture & Rules Established:**
  1. **Dynamic Model Configuration (Zero Hardcoding):**
     - LLM configuration is loaded from `.env` via `python-dotenv`.
     - `LLM_MODEL` is never hardcoded. If unconfigured or empty, the engine gracefully falls back to the deterministic playbook template generator (`is_fallback: True`).
     - Supports any OpenAI-compatible server endpoint (e.g., local Ollama, llama.cpp, vLLM, or remote OpenAI-compatible providers).
  2. **Prompt Builder & Grounding Pack (Section 5.6 & 5.7):**
     - System prompt enforces: evidence citation, strict priority parity (no re-ranking), prohibited phrase filtering (no guarantees/certainties), no hallucinated numbers or companies, and clean JSON generation.
     - User input is sandboxed within `<user_pitch>` data delimiters with explicit prompt injection defense instructions.
     - Grounding packs include verified model digest (A, B, C, D), provenance, report interpretation, prioritized issues, evidence index, and filtered playbook chunks.
  3. **Strict Schema & Grounding Validation (Section 5.9):**
     - `RecommendationValidator` parses JSON, validates schema conformity, requires non-empty text across all 7 plan fields, enforces at least 3 implementation steps, checks that every cited evidence reference exists in the grounding pack index, and scans regex patterns for prohibited guarantees.
  4. **One Repair Attempt (Section 5.9):**
     - On initial validation failure, `LLMClient` sends the validation error list back to the model with temperature lowered to 0.1 for precision correction.
     - If repair also fails, gracefully activates the template playbook fallback (`is_fallback: True`).
  5. **In-Memory Caching (Section 5.12):**
     - LLM responses are cached using a SHA-256 hash of `prompt_version:model:prompt` so identical evaluation requests yield identical outputs with zero latency and zero token consumption.
  6. **Offline Golden Set Evaluation (Section 5.12):**
     - Implemented `scripts/evaluate_recommendations.py` covering all 15 golden cases.
     - Achieved 100% validation pass rate, 100% grounding citation pass rate, 100% priority consistency rate, and 0% prohibited claims.
     - Generated `docs/recommendation_evaluation_report.md` with 10 sample outputs for human audit.

---

## Decision 008: Clarification Loop Versioning, Multi-Format Export, Privacy Deletion & Fault Isolation

- **Date:** 2026-10-29
- **Status:** Accepted
- **Context:** Step 5 implementation (Planning file 03 sections 3.8 and 3.9, Planning 04 sections 4.4, 4.7, 4.8, and Planning 05 section 5.11).
- **Architecture & Rules Established:**
  1. **Clarification Feedback Loop & Version Lineage:**
     - `POST /v1/evaluations/{id}/clarifications` receives answers to clarifying questions from Model C and the LLM.
     - Creates a newly linked version record (`v2`, `v3`, etc.) with `parent_id` and `root_id` tracking.
     - Merges clarified details into the startup pitch and relevant structured fields, re-normalizes, re-runs narrative models (C and D), and regenerates tailored recommendations.
     - Frontend provides interactive question input forms and a version switcher dropdown to compare report versions.
  2. **Multi-Format Export Engine (`backend/exporter.py`):**
     - `GET /v1/evaluations/{id}/export?format=json|html|pdf`:
       - `json`: Structured raw report and recommendations JSON with download attachment headers.
       - `html`: Beautiful, responsive, standalone single-file HTML report with embedded CSS styling.
       - `pdf`: High-quality multi-page PDF generated via ReportLab with synthesis banners, model sections, recommendation cards, and disclaimers.
  3. **Privacy & Complete Data Deletion:**
     - `DELETE /v1/evaluations/{id}` purges all evaluations, results, and lineage records from storage. Subsequent GET calls strictly return 404.
  4. **Robust Jobs & Fault Isolation:**
     - Per-model exception catching in `Orchestrator`: a failure or crash in one model (e.g. CUDA OOM or runtime failure) wraps the error in the envelope (`status="error"`) without breaking the entire run.
     - Report generation continues and surfaces partial results with trust panel warnings.
     - If all 4 models fail, the evaluation safely sets `status="failed"` with an explanatory message.
     - LLM outages or rate limits (e.g. HTTP 429) gracefully fall back to the deterministic playbook generator.


