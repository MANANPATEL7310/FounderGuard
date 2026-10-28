"""Report Builder: constructs sections 1 to 8 and overall interpretation."""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from backend.schemas.envelope import ModelEnvelope
from backend.schemas.report import (
    EvaluationMeta,
    EvaluationReport,
    InterpretationResult,
    ReportSection,
)

class ReportBuilder:
    @staticmethod
    def build_report(
        evaluation_id: str,
        normalized: Dict[str, Any],
        envelopes: Dict[str, ModelEnvelope],
        created_at: str,
    ) -> EvaluationReport:
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # 1. Determine Overall Interpretation
        interpretation = ReportBuilder._determine_interpretation(envelopes, normalized)

        # 2. Extract Key Factors
        key_factors = ReportBuilder._extract_key_factors(envelopes)

        # 3. Assemble Trust Panel
        trust = ReportBuilder._assemble_trust_panel(envelopes, normalized)

        # 4. Extract Issues List
        issues = ReportBuilder._extract_issues(envelopes)

        # 5. Build Evidence Index
        evidence_index = ReportBuilder._build_evidence_index(envelopes, normalized)

        # 6. Build the 8 Sections
        sections = ReportBuilder._build_sections(normalized, envelopes, interpretation, key_factors, trust, issues)

        meta = EvaluationMeta(
            evaluation_id=evaluation_id,
            created_at=created_at,
            completed_at=now_iso,
            model_versions={
                "model_a": "v1 (CatBoost)",
                "model_b": "v1 (LogisticRegression)",
                "model_c": "v1 (PyTorch BiGRU)",
                "model_d": "v1 (Multilabel LR)",
            }
        )

        input_summary = {
            "idea_description": normalized.get("idea_description"),
            "industry": normalized.get("industry"),
            "country": normalized.get("country"),
            "state": normalized.get("state"),
            "funding_total_usd": normalized.get("funding_total_usd"),
            "funding_rounds": normalized.get("funding_rounds"),
            "original_funding": normalized.get("original_funding"),
            "original_currency": normalized.get("original_currency"),
            "exchange_rate_used": normalized.get("exchange_rate_used"),
            "exchange_rate_date": normalized.get("exchange_rate_date"),
            "stage": normalized.get("stage"),
            "business_model": normalized.get("business_model"),
            "provenance": normalized.get("provenance", {})
        }

        return EvaluationReport(
            meta=meta,
            input_summary=input_summary,
            models=envelopes,
            interpretation=interpretation,
            key_factors=key_factors,
            trust=trust,
            issues=issues,
            evidence_index=evidence_index,
            sections=sections,
        )

    @staticmethod
    def _determine_interpretation(envelopes: Dict[str, ModelEnvelope], normalized: Dict[str, Any]) -> InterpretationResult:
        env_a = envelopes.get("model_a")
        env_b = envelopes.get("model_b")
        env_c = envelopes.get("model_c")
        env_d = envelopes.get("model_d")

        # Count unavailable or not applicable models
        non_ok_count = sum(1 for e in [env_a, env_b, env_c, env_d] if not e or e.status != "ok")
        
        # Model D OOD check
        d_ood = False
        if env_d and env_d.status == "ok" and env_d.data:
            d_ood = env_d.data.get("ood", {}).get("flagged", False)

        # Condition 4: Insufficient basis
        if non_ok_count >= 2 or (d_ood and (not env_b or env_b.status != "ok")):
            reasons = []
            if env_b and env_b.status == "not_applicable":
                reasons.append(f"Model B: {env_b.applicability_reason}")
            if env_a and env_a.status == "not_applicable":
                reasons.append(f"Model A: {env_a.applicability_reason}")
            if non_ok_count >= 2:
                reasons.append(f"{non_ok_count} models were not applicable or unavailable for this stage/input.")
            if d_ood:
                reasons.append("Model D text narrative was flagged as out-of-distribution.")
            return InterpretationResult(
                category="Insufficient basis",
                summary="The available quantitative financial and cohort data is insufficient to establish a complete multi-model outcome prediction (e.g. pre-funding idea stage or missing cohort dates). Qualitative text analysis remains available below.",
                reasons=reasons
            )

        # Check Model B risk level
        b_level = env_b.data.get("risk_level") if (env_b and env_b.status == "ok" and env_b.data) else "Unknown"
        b_is_high = b_level in ("High", "Very High")
        b_is_low = b_level in ("Low", "Moderate")

        # Check Model A leaning
        a_leans_closure = False
        if env_a and env_a.status == "ok" and env_a.data:
            a_leans_closure = env_a.data.get("predicted_class") == 0 or env_a.data.get("probabilities", {}).get("closed", 0.0) >= 0.5

        # Check Model D categories count
        d_pred_cats = env_d.data.get("predicted_categories", []) if (env_d and env_d.status == "ok" and env_d.data) else []
        d_multiple_cats = len(d_pred_cats) >= 2

        # Condition 1: Elevated concern
        if b_is_high and (a_leans_closure or d_multiple_cats):
            reasons = [f"Model B assessed failure risk as {b_level}."]
            if a_leans_closure:
                reasons.append("Model A predicted class leans toward Closure.")
            if d_multiple_cats:
                reasons.append(f"Model D detected {len(d_pred_cats)} historical failure themes: {', '.join(d_pred_cats)}.")
            return InterpretationResult(
                category="Elevated concern",
                summary="Multiple analytical models indicate heightened vulnerability. Both historical cohort outcomes and text-derived failure themes suggest significant structural hurdles.",
                reasons=reasons
            )

        # Condition 2: Mixed picture
        if (b_is_low and d_multiple_cats) or (b_is_high and not a_leans_closure and not d_multiple_cats):
            reasons = [
                f"Model B indicated {b_level} financial failure risk.",
                f"Model D predicted {len(d_pred_cats)} failure categories.",
            ]
            if env_a and env_a.status == "ok" and env_a.data:
                reasons.append(f"Model A predicted: {env_a.data.get('predicted_outcome')}.")
            return InterpretationResult(
                category="Mixed picture",
                summary="The models present divergent signals. While certain financial or historical signals are reassuring, qualitative risk patterns or cohort metrics flag potential friction points.",
                reasons=reasons
            )

        # Condition 3: Lower concern, under-evidenced
        not_stated_count = 0
        if env_c and env_c.status == "ok" and env_c.data:
            aspects = env_c.data.get("aspect_findings", [])
            not_stated_count = sum(1 for a in aspects if a.get("status") == "not_stated")

        if b_is_low and not_stated_count >= 4:
            return InterpretationResult(
                category="Lower concern, under-evidenced",
                summary="Quantitative failure risk appears modest based on current profile, but key qualitative validation dimensions (customer specificity, demand validation, traction) are unstated in the pitch.",
                reasons=[
                    f"Model B indicated {b_level} risk.",
                    f"{not_stated_count} of 8 key business aspects are not stated in the submitted description.",
                ]
            )

        # Default fallback to Mixed picture / balanced
        return InterpretationResult(
            category="Mixed picture",
            summary="Models evaluated the startup across distinct operational dimensions without converging on a single extreme outcome.",
            reasons=["Profile exhibits balanced signals across cohort and text analyses."]
        )

    @staticmethod
    def _extract_key_factors(envelopes: Dict[str, ModelEnvelope]) -> Dict[str, List[Dict[str, Any]]]:
        out = {}
        # Model A
        env_a = envelopes.get("model_a")
        if env_a and env_a.status == "ok" and env_a.data:
            out["model_a"] = env_a.data.get("top_contributing_features", [])
        
        # Model B
        env_b = envelopes.get("model_b")
        if env_b and env_b.status == "ok" and env_b.data:
            out["model_b"] = env_b.data.get("top_contributing_features", [])

        # Model C
        env_c = envelopes.get("model_c")
        if env_c and env_c.status == "ok" and env_c.data:
            terms = env_c.data.get("key_terms_attended_by_nn", [])
            out["model_c"] = [{"term": t, "type": "attended_term"} for t in terms]

        # Model D
        env_d = envelopes.get("model_d")
        if env_d and env_d.status == "ok" and env_d.data:
            cats = env_d.data.get("categories", [])
            out["model_d"] = [
                {"category": c["label"], "probability": c["probability"], "evidence": c.get("evidence_sentence")}
                for c in cats if c.get("predicted")
            ]
        return out

    @staticmethod
    def _assemble_trust_panel(envelopes: Dict[str, ModelEnvelope], normalized: Dict[str, Any]) -> Dict[str, Any]:
        all_warnings = []
        limitations = []
        validation_status = {}

        for m_id, env in envelopes.items():
            if env:
                all_warnings.extend([f"[{m_id}] {w}" for w in env.warnings])
                if env.data and "limitations" in env.data:
                    limitations.extend(env.data["limitations"])
                if env.data and "validation_status" in env.data:
                    validation_status[m_id] = env.data["validation_status"]

        return {
            "warnings": all_warnings,
            "provenance": normalized.get("provenance", {}),
            "currency_conversion": {
                "original": f"{normalized.get('original_funding')} {normalized.get('original_currency')}",
                "converted_usd": f"${normalized.get('funding_total_usd'):,.2f} USD",
                "rate": normalized.get("exchange_rate_used"),
                "date": normalized.get("exchange_rate_date"),
            },
            "validation_status": validation_status,
            "general_limitations": [
                "Models provide statistical approximations from historical datasets; they do not guarantee success or failure.",
                "Unstated fields reflect omitted pitch information, not confirmed negative facts.",
                "Predictions reflect historical macroeconomic periods and may not fully capture current market dynamics.",
            ],
        }

    @staticmethod
    def _extract_issues(envelopes: Dict[str, ModelEnvelope]) -> List[Dict[str, Any]]:
        issues = []
        # Issues from Model D
        env_d = envelopes.get("model_d")
        if env_d and env_d.status == "ok" and env_d.data:
            for cat in env_d.data.get("categories", []):
                if cat.get("predicted"):
                    issues.append({
                        "id": f"issue_d_{cat['category']}",
                        "source": "Model D (Failure Narratives)",
                        "severity": "High" if cat["probability"] >= 0.7 else "Moderate",
                        "title": f"Risk Theme: {cat['label']}",
                        "evidence": cat.get("evidence_sentence"),
                        "probability": cat["probability"],
                    })

        # Issues from Model C
        env_c = envelopes.get("model_c")
        if env_c and env_c.status == "ok" and env_c.data:
            for gap in env_c.data.get("potential_weaknesses_and_gaps", []):
                issues.append({
                    "id": f"issue_c_{str(uuid.uuid4())[:8]}",
                    "source": "Model C (Qualitative Pitch Analysis)",
                    "severity": "Moderate" if "Vague" not in gap["aspect"] else "Low",
                    "title": f"Gap in {gap['aspect']}",
                    "evidence": gap.get("detail", ""),
                })

        # Issues from Model B
        env_b = envelopes.get("model_b")
        if env_b and env_b.status == "ok" and env_b.data:
            if env_b.data.get("risk_level") in ("High", "Very High"):
                issues.append({
                    "id": "issue_b_risk",
                    "source": "Model B (Financial Cohort Risk)",
                    "severity": "High",
                    "title": f"High Relative Failure Risk ({env_b.data.get('risk_score')}/100)",
                    "evidence": env_b.data.get("meaning", ""),
                })

        return issues

    @staticmethod
    def _build_evidence_index(envelopes: Dict[str, ModelEnvelope], normalized: Dict[str, Any]) -> Dict[str, Any]:
        idx = {}
        # User input facts
        idx["user_pitch"] = normalized.get("idea_description")
        idx["user_funding_usd"] = normalized.get("funding_total_usd")

        # Model A outcome evidence
        env_a = envelopes.get("model_a")
        if env_a and env_a.status == "ok" and env_a.data:
            idx["a_outcome_lean"] = f"Model A cohort outcome lean: {env_a.data.get('outcome_label')}"

        # Model B financial risk evidence
        env_b = envelopes.get("model_b")
        if env_b and env_b.status == "ok" and env_b.data:
            idx["b_financial_risk"] = f"Model B relative risk: {env_b.data.get('risk_score')}/100 ({env_b.data.get('risk_level')})"

        # Model C quotes and aspect references
        env_c = envelopes.get("model_c")
        if env_c and env_c.status == "ok" and env_c.data:
            for s in env_c.data.get("strengths", []):
                idx[f"c_strength_{s['aspect']}"] = s.get("supporting_text", [])
            for a in env_c.data.get("aspect_findings", []):
                asp = str(a.get("aspect", "")).lower()
                evidence_list = a.get("evidence", [])
                ev_quote = evidence_list[0] if evidence_list else a.get("note", "")
                idx[f"c_aspect_{asp}"] = ev_quote
            # Index general theme aspect keys
            for t in ["product_market_fit", "idea_clarity", "acquisition_retention", "validation_evidence", "market_demand", "competition_differentiation", "weak_business_model", "unit_economics_pricing", "execution_hurdles"]:
                idx[f"c_aspect_{t}"] = f"Model C analysis for theme: {t}"

        # Model D evidence sentences
        env_d = envelopes.get("model_d")
        if env_d and env_d.status == "ok" and env_d.data:
            for c in env_d.data.get("categories", []):
                if c.get("evidence_sentence"):
                    idx[f"d_evidence_{c['category']}"] = c["evidence_sentence"]

        return idx

    @staticmethod
    def _build_sections(
        normalized: Dict[str, Any],
        envelopes: Dict[str, ModelEnvelope],
        interpretation: InterpretationResult,
        key_factors: Dict[str, Any],
        trust: Dict[str, Any],
        issues: List[Dict[str, Any]],
    ) -> List[ReportSection]:
        # Section 1: Executive Summary
        exec_summary = (
            f"{normalized.get('industry')} startup at stage '{normalized.get('stage')}' based in {normalized.get('country')}. "
            f"Funding reported: ${normalized.get('funding_total_usd'):,.2f} USD across {normalized.get('funding_rounds')} rounds. "
            f"Overall evaluation: {interpretation.category}. {interpretation.summary}"
        )
        sec_1 = ReportSection(
            section_number=1,
            title="Executive Summary",
            content={"summary_text": exec_summary, "interpretation": interpretation.model_dump()}
        )

        # Section 2: Model A (Predicted outcome)
        env_a = envelopes.get("model_a")
        sec_2 = ReportSection(
            section_number=2,
            title="Predicted Outcome and Probabilities (Model A)",
            content={"envelope": env_a.model_dump() if env_a else None}
        )

        # Section 3: Model B (Failure Risk Score)
        env_b = envelopes.get("model_b")
        sec_3 = ReportSection(
            section_number=3,
            title="Failure Probability and Risk Score (Model B)",
            content={"envelope": env_b.model_dump() if env_b else None}
        )

        # Section 4: Model C (Idea Evaluation & Aspect Findings)
        env_c = envelopes.get("model_c")
        sec_4 = ReportSection(
            section_number=4,
            title="Idea Evaluation, Strengths & Missing Evidence (Model C)",
            content={"envelope": env_c.model_dump() if env_c else None}
        )

        # Section 5: Model D (Failure Categories & Post-Mortem Evidence)
        env_d = envelopes.get("model_d")
        sec_5 = ReportSection(
            section_number=5,
            title="Failure Categories & Historical Evidence (Model D)",
            content={"envelope": env_d.model_dump() if env_d else None}
        )

        # Section 6: Key Factors
        sec_6 = ReportSection(
            section_number=6,
            title="Key Contributing Factors",
            content={"factors_by_model": key_factors}
        )

        # Section 7: Assumptions, Uncertainty & Trust
        sec_7 = ReportSection(
            section_number=7,
            title="Assumptions, Limitations & Trust Panel",
            content=trust
        )

        # Section 8: Overall Assessment and Next Steps
        sec_8 = ReportSection(
            section_number=8,
            title="Overall Assessment & Next Steps",
            content={
                "interpretation": interpretation.model_dump(),
                "identified_issues": issues,
                "recommendations_status": "Recommendations engine placeholder (Step 3/4 activation).",
            }
        )

        return [sec_1, sec_2, sec_3, sec_4, sec_5, sec_6, sec_7, sec_8]

