"""Deterministic Issue Prioritizer according to Section 5.4 of the specification."""
from typing import Any, Dict, List, Optional, Set, Tuple
from backend.schemas.envelope import ModelEnvelope
from backend.schemas.recommendation import PrioritizedIssue

THEMES = [
    "market_demand",
    "funding_cashflow",
    "competition_differentiation",
    "unit_economics_pricing",
    "acquisition_retention",
    "team_operations",
    "weak_business_model",
    "product_market_fit",
    "idea_clarity",
    "validation_evidence",
    "execution_hurdles",
]

THEME_TITLES = {
    "market_demand": "Validation of Market Demand & Problem Urgency",
    "funding_cashflow": "Capital Runway & Cash-Flow Sustainability",
    "competition_differentiation": "Competitive Differentiation & Value Wedge",
    "unit_economics_pricing": "Pricing Strategy & Unit Economic Viability",
    "acquisition_retention": "Customer Acquisition & Retention Dynamics",
    "team_operations": "Team Capabilities & Operational Execution",
    "weak_business_model": "Business Model Structure & Monetization",
    "product_market_fit": "Problem-Solution Fit & User Satisfaction",
    "idea_clarity": "Value Proposition Clarity & Solution Specificity",
    "validation_evidence": "Customer Discovery & Empirical Evidence",
    "execution_hurdles": "Execution Feasibility & Operational Roadblocks",
}


class IssuePrioritizer:
    @staticmethod
    def prioritize_issues(
        envelopes: Dict[str, ModelEnvelope],
        normalized: Dict[str, Any],
        evidence_index: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[PrioritizedIssue], List[Dict[str, Any]]]:
        """
        Maps signals across Models A, B, C, and D into shared themes, applies deterministic
        priority assignment rules (High, Medium, Low), enforces OOD capping, and returns
        the top 6 prioritized issues along with remaining other observations.
        """
        theme_signals: Dict[str, Dict[str, Any]] = {
            t: {
                "models": set(),
                "strong_models": set(),
                "evidence_refs": [],
                "evidence_quotes": [],
                "is_gap_only": True,
                "notes": [],
                "d_predicted": False,
                "d_label_quality": "acceptable",
                "d_prob": 0.0,
            }
            for t in THEMES
        }

        # ── 1. Extract Signals from Model D ──────────────────────────────────────────
        env_d = envelopes.get("model_d")
        d_ood = False
        if env_d and env_d.status == "ok" and env_d.data:
            d_ood = env_d.data.get("ood", {}).get("flagged", False)
            for c in env_d.data.get("categories", []):
                cat_id = c.get("category")
                if cat_id in theme_signals:
                    prob = float(c.get("probability", 0.0))
                    pred = bool(c.get("predicted", False))
                    lq = str(c.get("label_quality", "acceptable"))
                    theme_signals[cat_id]["d_prob"] = prob
                    theme_signals[cat_id]["d_label_quality"] = lq

                    if pred or prob >= 0.40:
                        theme_signals[cat_id]["models"].add("model_d")
                        theme_signals[cat_id]["is_gap_only"] = False
                        ev_sent = c.get("evidence_sentence")
                        if ev_sent:
                            theme_signals[cat_id]["evidence_quotes"].append(ev_sent)
                            theme_signals[cat_id]["evidence_refs"].append(f"d_evidence_{cat_id}")

                        if pred:
                            theme_signals[cat_id]["d_predicted"] = True
                            theme_signals[cat_id]["strong_models"].add("model_d")
                            theme_signals[cat_id]["notes"].append(
                                f"Model D flagged historical failure theme ({prob*100:.1f}% similarity)"
                            )
                        else:
                            theme_signals[cat_id]["notes"].append(
                                f"Model D moderate signal ({prob*100:.1f}% similarity)"
                            )

        # ── 2. Extract Signals from Model C ──────────────────────────────────────────
        env_c = envelopes.get("model_c")
        if env_c and env_c.status == "ok" and env_c.data:
            aspects = env_c.data.get("aspect_findings", [])
            for a in aspects:
                asp_name = str(a.get("aspect", "")).lower()
                status = str(a.get("status", "not_stated")).lower()
                evidence_list = a.get("evidence", [])
                ev_quote = evidence_list[0] if evidence_list else a.get("note", "")

                target_themes: List[str] = []
                if "problem" in asp_name:
                    target_themes = ["product_market_fit", "idea_clarity"]
                elif "target customer" in asp_name or "customer" in asp_name:
                    target_themes = ["acquisition_retention"]
                elif "solution" in asp_name:
                    target_themes = ["idea_clarity"]
                elif "validation" in asp_name or "demand" in asp_name:
                    target_themes = ["validation_evidence", "market_demand"]
                elif "competitor" in asp_name or "differentiat" in asp_name:
                    target_themes = ["competition_differentiation"]
                elif "business model" in asp_name or "pricing" in asp_name:
                    target_themes = ["weak_business_model", "unit_economics_pricing"]
                elif "feasibility" in asp_name or "execution" in asp_name:
                    target_themes = ["execution_hurdles"]

                for t in target_themes:
                    if t in theme_signals:
                        if status in ("not_stated", "partial", "risk_signals_found"):
                            theme_signals[t]["models"].add("model_c")
                            ref_id = f"c_aspect_{t}"
                            if ref_id not in theme_signals[t]["evidence_refs"]:
                                theme_signals[t]["evidence_refs"].append(ref_id)
                            if ev_quote and ev_quote not in theme_signals[t]["evidence_quotes"]:
                                theme_signals[t]["evidence_quotes"].append(f"Model C: {ev_quote}")

                            if status == "risk_signals_found":
                                theme_signals[t]["strong_models"].add("model_c")
                                theme_signals[t]["is_gap_only"] = False
                                theme_signals[t]["notes"].append("Model C detected risk signals in pitch")
                            else:
                                theme_signals[t]["notes"].append(f"Model C aspect '{a.get('aspect')}' is {status}")

            # Check vague terms
            vague_terms = env_c.data.get("vague_terms", [])
            if vague_terms:
                theme_signals["idea_clarity"]["models"].add("model_c")
                theme_signals["idea_clarity"]["notes"].append(
                    f"Model C detected {len(vague_terms)} buzzwords ({', '.join(vague_terms[:3])})"
                )

        # ── 3. Extract Signals from Model B ──────────────────────────────────────────
        env_b = envelopes.get("model_b")
        b_is_high = False
        if env_b and env_b.status == "ok" and env_b.data:
            b_level = env_b.data.get("risk_level", "Low")
            b_is_high = b_level in ("High", "Very High")
            top_factors = env_b.data.get("top_contributing_features", [])

            # Check if risk level is high or factors raise risk
            has_raising_factor = any(f.get("direction") == "raises" for f in top_factors)
            if b_is_high or has_raising_factor:
                theme_signals["funding_cashflow"]["models"].add("model_b")
                theme_signals["funding_cashflow"]["is_gap_only"] = False
                theme_signals["funding_cashflow"]["evidence_refs"].append("b_financial_risk")
                theme_signals["funding_cashflow"]["evidence_quotes"].append(
                    f"Model B relative failure risk: {env_b.data.get('risk_score')}/100 ({b_level})"
                )
                if b_is_high:
                    theme_signals["funding_cashflow"]["strong_models"].add("model_b")
                    theme_signals["funding_cashflow"]["notes"].append(f"Model B failure risk assessed as {b_level}")
                else:
                    theme_signals["funding_cashflow"]["notes"].append("Model B top factors raise financial risk")

        # ── 4. Extract Signals from Model A ──────────────────────────────────────────
        env_a = envelopes.get("model_a")
        if env_a and env_a.status == "ok" and env_a.data:
            pred_class = env_a.data.get("predicted_class", 1)
            p_closed = env_a.data.get("probabilities", {}).get("closed", 0.0)
            if pred_class == 0 or p_closed >= 0.50:
                theme_signals["funding_cashflow"]["models"].add("model_a")
                theme_signals["funding_cashflow"]["is_gap_only"] = False
                theme_signals["funding_cashflow"]["evidence_refs"].append("a_outcome_lean")
                theme_signals["funding_cashflow"]["evidence_quotes"].append(
                    f"Model A historical cohort lean: Closed ({p_closed*100:.1f}%)"
                )
                theme_signals["funding_cashflow"]["strong_models"].add("model_a")
                theme_signals["funding_cashflow"]["notes"].append("Model A predicted cohort outcome leans toward Closure")

        # ── 5. Assign Priorities Deterministically ──────────────────────────────────
        prioritized_list: List[PrioritizedIssue] = []

        for theme, sig in theme_signals.items():
            models_count = len(sig["models"])
            strong_count = len(sig["strong_models"])
            if models_count == 0:
                continue

            priority = "Low"

            # Rule 1: High Priority
            # - Theme supported by two or more different models
            # - Model D predicts it clearly with acceptable label quality
            # - Model B factor matches and B is High or Very High
            if models_count >= 2:
                priority = "High"
            elif sig["d_predicted"] and sig["d_label_quality"] != "low":
                priority = "High"
            elif "model_b" in sig["strong_models"] and b_is_high:
                priority = "High"
            elif strong_count >= 1:
                priority = "Medium"
            elif not sig["is_gap_only"]:
                priority = "Medium"
            else:
                priority = "Low"

            # Rule 2: OOD Capping
            # If Model D OOD is flagged and the issue is supported ONLY by Model D, cap at Medium
            if d_ood and sig["models"] == {"model_d"} and priority == "High":
                priority = "Medium"
                sig["notes"].append("Capped at Medium due to Model D out-of-distribution text")

            # Confidence Note
            conf_note = "; ".join(sig["notes"]) if sig["notes"] else "Identified from input signals"

            prioritized_list.append(
                PrioritizedIssue(
                    id=f"issue_{theme}",
                    theme=theme,
                    title=THEME_TITLES.get(theme, theme.replace("_", " ").title()),
                    priority=priority,
                    supporting_models=sorted(list(sig["models"])),
                    evidence_refs=sig["evidence_refs"],
                    evidence_quotes=sig["evidence_quotes"],
                    confidence_note=conf_note,
                    is_gap_only=sig["is_gap_only"],
                )
            )

        # ── 6. Sort and Rank (Top 6 vs Other Observations) ──────────────────────────
        prio_weight = {"High": 3, "Medium": 2, "Low": 1}

        def sort_key(issue: PrioritizedIssue):
            # Sort by priority, then non-gap before gap, then number of supporting models
            return (
                prio_weight.get(issue.priority, 1),
                0 if not issue.is_gap_only else -1,
                len(issue.supporting_models),
            )

        prioritized_list.sort(key=sort_key, reverse=True)

        # If no issues were identified (e.g. pristine pitch with 0 models flagging anything),
        # supply default baseline discovery & validation issues
        if not prioritized_list:
            prioritized_list.append(
                PrioritizedIssue(
                    id="issue_validation_evidence",
                    theme="validation_evidence",
                    title=THEME_TITLES["validation_evidence"],
                    priority="Medium",
                    supporting_models=[],
                    confidence_note="Baseline discovery recommended for early stage startups",
                    is_gap_only=True,
                )
            )

        top_issues = prioritized_list[:6]
        other_obs = [
            {
                "id": iss.id,
                "theme": iss.theme,
                "title": iss.title,
                "priority": iss.priority,
                "supporting_models": iss.supporting_models,
                "confidence_note": iss.confidence_note,
            }
            for iss in prioritized_list[6:]
        ]

        return top_issues, other_obs

