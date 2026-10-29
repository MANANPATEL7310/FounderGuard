# Recommendation Evaluation Report (Section 5.12)

**Evaluated on:** 15 Golden Submissions  
**Target:** Verify Schema Validation, Groundedness, Priority Consistency, and Prohibited Phrase Filtering.

## Summary Metrics
- **Total Golden Cases:** 15
- **Validation Pass Rate:** 15/15 (100.0%)
- **Grounding Citation Pass Rate:** 15/15 (100.0%)
- **Priority Consistency Rate:** 15/15 (100.0%)
- **Absence of Prohibited Guarantees:** 15/15 (100.0%)
- **Generation Method Breakdown:**
  - `llm_direct`: 3 cases
  - `template_playbook`: 12 cases

## Sample Outputs (10 Cases for Human Inspection)

### Case: `golden_01_funded_us_enterprise_ai` (N/A - Artificial Intelligence / ML, growing)
- **Method:** `llm_direct` (fallback: False)
- **Recommendations Count:** 1
  - **[HIGH] Capital Runway & Cash-Flow Sustainability**
    - *Action:* Build a rolling 18‑month zero‑based cash‑flow model and align future fundraising milestones with key product milestones.
    - *Validation Method:* Maintain a minimum of 9 months of cash runway at all times and keep monthly burn variance within 10% of forecast, verified within the next 30 days.
    - *Steps:* Step 1: Assemble all current revenue, burn, and vendor commitments to create a detailed monthly cash‑flow forecast for the next 18 months.; Step 2: Calculate the current net runway (cash on hand ÷ monthly net burn) and identify the month when runway falls below 6 months.; Step 3: Define three valuation‑inflection milestones (e.g., 10 paying underwriters, $15k MRR, regulatory approval) and map each to a fundraising round or capital injection.
- **Clarifying Questions:**
  - *Financials:* What is the current monthly burn rate and how is it split between fixed and variable costs?
  - *Revenue:* What are the projected revenue streams and timelines for reaching the 10 paying customers and $15k MRR milestones?

---
### Case: `golden_02_prefunding_idea_us` (N/A - Consumer Apps & Social, idea)
- **Method:** `llm_direct` (fallback: False)
- **Recommendations Count:** 1
  - **[MEDIUM] Customer Discovery & Empirical Evidence**
    - *Action:* Execute a structured problem discovery interview program targeting remote freelancers who use boutique hotel lounges.
    - *Validation Method:* Achieve a metric of ≥60% of interviewees reporting the problem causes weekly friction and describing a costly workaround, completing 20 interviews within 3 weeks.
    - *Steps:* Step 1: Define a screener that captures remote freelancers who have used or considered using hotel lounge spaces, including job title, industry, and typical remote work hours.; Step 2: Draft an interview guide focused on past behaviors and current workarounds, following the principles of 'The Mom Test' to avoid solution bias.; Step 3: Reach out to 50–80 prospects via cold email, alumni networks, and relevant online communities, offering a small incentive for participation.
- **Clarifying Questions:**
  - *Target customer profile:* What specific job titles, industries, or company sizes define your ideal remote freelancer customer?
  - *Outreach feasibility:* Do you currently have any contacts or community memberships that could help you reach potential interviewees quickly?

---
### Case: `golden_03_funded_non_us_fintech` (N/A - FinTech & Financial Services, launched)
- **Method:** `llm_direct` (fallback: False)
- **Recommendations Count:** 1
  - **[HIGH] Capital Runway & Cash-Flow Sustainability**
    - *Action:* Build a rolling 18‑month cashflow model and tie fundraising milestones directly to derisked product milestones.
    - *Validation Method:* Maintain a minimum of 9 months of cash runway at all times, with monthly burn variance within 10% of forecast, verified within 30 days.
    - *Steps:* Step 1: Create a detailed zero‑based monthly cashflow model showing fixed vs variable burn.; Step 2: Calculate current net runway in months (cash in bank ÷ monthly net burn).; Step 3: Identify 3 concrete valuation‑inflection milestones (e.g., 10 paying customers, $15k MRR, key regulatory approval).
- **Clarifying Questions:**
  - *Financials:* What is the current cash balance and monthly net burn rate?
  - *Revenue:* What are the projected revenue milestones for the next 12 months?

---
### Case: `golden_04_funded_us_missing_dates` (N/A - Healthcare, Biotech & Life Sciences, MVP)
- **Method:** `template_playbook` (fallback: True)
- **Recommendations Count:** 1
  - **[HIGH] Capital Runway & Cash-Flow Sustainability**
    - *Action:* Build a rolling 18-month cashflow model and tie fundraising milestones directly to derisked product milestones.
    - *Validation Method:* Metric: Minimum 9 months of cash runway maintained at all times, with monthly burn variance within 10% of forecast.
    - *Steps:* Create a detailed zero-based monthly cashflow model showing fixed vs variable monthly burn rate.; Calculate current net runway in months (cash in bank divided by monthly net burn).; Identify 3 concrete valuation-inflection milestones (e.g. 10 paying customers, $15k MRR, key regulatory approval).

---
### Case: `golden_05_prefunding_healthcare_deep_validation` (N/A - Healthcare, Biotech & Life Sciences, validation)
- **Method:** `template_playbook` (fallback: True)
- **Recommendations Count:** 1
  - **[MEDIUM] Customer Discovery & Empirical Evidence**
    - *Action:* Conduct 20–30 structured problem discovery interviews with target buyers without pitching the solution.
    - *Validation Method:* Metric: >= 60% of interviewees report the problem causes weekly friction and describe a costly current workaround. Target: 20 interviews completed within 3 weeks.
    - *Steps:* Define an exact screener targeting your ideal customer profile (title, industry, company size).; Draft an interview guide focused on past behaviors and current painful workarounds (following 'The Mom Test').; Reach out to 50–80 prospects via cold outreach, alumni networks, or specialized online communities.

---
### Case: `golden_06_funded_biotech_scaleup` (N/A - Healthcare, Biotech & Life Sciences, growing)
- **Method:** `template_playbook` (fallback: True)
- **Recommendations Count:** 1
  - **[HIGH] Capital Runway & Cash-Flow Sustainability**
    - *Action:* Build a rolling 18-month cashflow model and tie fundraising milestones directly to derisked product milestones.
    - *Validation Method:* Metric: Minimum 9 months of cash runway maintained at all times, with monthly burn variance within 10% of forecast.
    - *Steps:* Create a detailed zero-based monthly cashflow model showing fixed vs variable monthly burn rate.; Calculate current net runway in months (cash in bank divided by monthly net burn).; Identify 3 concrete valuation-inflection milestones (e.g. 10 paying customers, $15k MRR, key regulatory approval).

---
### Case: `golden_07_temporal_drift_recent_year_2025` (N/A - Security & Cybersecurity, launched)
- **Method:** `template_playbook` (fallback: True)
- **Recommendations Count:** 1
  - **[HIGH] Capital Runway & Cash-Flow Sustainability**
    - *Action:* Build a rolling 18-month cashflow model and tie fundraising milestones directly to derisked product milestones.
    - *Validation Method:* Metric: Minimum 9 months of cash runway maintained at all times, with monthly burn variance within 10% of forecast.
    - *Steps:* Create a detailed zero-based monthly cashflow model showing fixed vs variable monthly burn rate.; Calculate current net runway in months (cash in bank divided by monthly net burn).; Identify 3 concrete valuation-inflection milestones (e.g. 10 paying customers, $15k MRR, key regulatory approval).

---
### Case: `golden_08_short_pitch_minimal` (N/A - Consumer Apps & Social, launched)
- **Method:** `template_playbook` (fallback: True)
- **Recommendations Count:** 1
  - **[HIGH] Capital Runway & Cash-Flow Sustainability**
    - *Action:* Build a rolling 18-month cashflow model and tie fundraising milestones directly to derisked product milestones.
    - *Validation Method:* Metric: Minimum 9 months of cash runway maintained at all times, with monthly burn variance within 10% of forecast.
    - *Steps:* Create a detailed zero-based monthly cashflow model showing fixed vs variable monthly burn rate.; Calculate current net runway in months (cash in bank divided by monthly net burn).; Identify 3 concrete valuation-inflection milestones (e.g. 10 paying customers, $15k MRR, key regulatory approval).

---
### Case: `golden_09_ecommerce_marketplace_traction` (N/A - E-Commerce & Marketplaces, growing)
- **Method:** `template_playbook` (fallback: True)
- **Recommendations Count:** 1
  - **[HIGH] Capital Runway & Cash-Flow Sustainability**
    - *Action:* Build a rolling 18-month cashflow model and tie fundraising milestones directly to derisked product milestones.
    - *Validation Method:* Metric: Minimum 9 months of cash runway maintained at all times, with monthly burn variance within 10% of forecast.
    - *Steps:* Create a detailed zero-based monthly cashflow model showing fixed vs variable monthly burn rate.; Calculate current net runway in months (cash in bank divided by monthly net burn).; Identify 3 concrete valuation-inflection milestones (e.g. 10 paying customers, $15k MRR, key regulatory approval).

---
### Case: `golden_10_cleantech_hardware_seed` (N/A - CleanTech & Energy, MVP)
- **Method:** `template_playbook` (fallback: True)
- **Recommendations Count:** 1
  - **[HIGH] Capital Runway & Cash-Flow Sustainability**
    - *Action:* Build a rolling 18-month cashflow model and tie fundraising milestones directly to derisked product milestones.
    - *Validation Method:* Metric: Minimum 9 months of cash runway maintained at all times, with monthly burn variance within 10% of forecast.
    - *Steps:* Create a detailed zero-based monthly cashflow model showing fixed vs variable monthly burn rate.; Calculate current net runway in months (cash in bank divided by monthly net burn).; Identify 3 concrete valuation-inflection milestones (e.g. 10 paying customers, $15k MRR, key regulatory approval).

---
