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
