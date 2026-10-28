"""Grounding Pack Builder: assembles structured evidence according to Section 5.6."""
from typing import Any, Dict, List
from backend.recommendations.playbook import playbook_kb
from backend.recommendations.prioritizer import IssuePrioritizer
from backend.schemas.envelope import ModelEnvelope
from backend.schemas.recommendation import PrioritizedIssue


class GroundingPackBuilder:
    @staticmethod
    def build_grounding_pack(
        evaluation_id: str,
        normalized: Dict[str, Any],
        envelopes: Dict[str, ModelEnvelope],
        report: Any = None,
    ) -> Dict[str, Any]:
        """
        Assembles a bounded, structured grounding pack for the LLM containing
        verified model signals, input provenance, prioritized issues, and playbook chunks.
        """
        stage = normalized.get("stage", "idea")
        industry = normalized.get("industry", "Technology")

        # 1. User Profile & Provenance
        user_profile = {
            "idea_description": normalized.get("idea_description", ""),
            "industry": industry,
            "country": normalized.get("country", ""),
            "state": normalized.get("state"),
            "stage": stage,
            "target_market": normalized.get("target_market", "global"),
            "business_model": normalized.get("business_model", []),
            "funding_total_usd": normalized.get("funding_total_usd", 0.0),
            "funding_rounds": normalized.get("funding_rounds", 0),
            "team_size": normalized.get("team_size", 1),
            "team_skills": normalized.get("team_skills", []),
            "founder_experience": normalized.get("founder_experience", "first-time"),
            "provenance_provided": normalized.get("provenance", {}).get("provided_fields", []),
            "provenance_missing": normalized.get("provenance", {}).get("missing_fields", []),
        }

        # 2. Model Digest
        model_digest: Dict[str, Any] = {}

        # Model A
        env_a = envelopes.get("model_a")
        if env_a and env_a.status == "ok" and env_a.data:
            model_digest["model_a"] = {
                "status": "ok",
                "predicted_outcome": env_a.data.get("predicted_outcome"),
                "probabilities": env_a.data.get("probabilities"),
                "confidence": env_a.data.get("confidence"),
                "target_definition": env_a.data.get("target_definition"),
            }
        else:
            model_digest["model_a"] = {
                "status": env_a.status if env_a else "unavailable",
                "reason": env_a.applicability_reason if env_a else "Not executed",
            }

        # Model B
        env_b = envelopes.get("model_b")
        if env_b and env_b.status == "ok" and env_b.data:
            model_digest["model_b"] = {
                "status": "ok",
                "risk_score": env_b.data.get("risk_score"),
                "risk_level": env_b.data.get("risk_level"),
                "meaning": env_b.data.get("meaning"),
                "top_factors": env_b.data.get("top_contributing_features", [])[:3],
            }
        else:
            model_digest["model_b"] = {
                "status": env_b.status if env_b else "unavailable",
                "reason": env_b.applicability_reason if env_b else "Not executed",
            }

        # Model C
        env_c = envelopes.get("model_c")
        if env_c and env_c.status == "ok" and env_c.data:
            model_digest["model_c"] = {
                "status": "ok",
                "sector_check": env_c.data.get("sector_check"),
                "vague_terms": env_c.data.get("vague_terms", [])[:5],
                "aspects": [
                    {"aspect": a.get("aspect"), "status": a.get("status"), "evidence": a.get("evidence", [])[:1]}
                    for a in env_c.data.get("aspect_findings", [])
                ],
            }
        else:
            model_digest["model_c"] = {"status": "unavailable"}

        # Model D
        env_d = envelopes.get("model_d")
        if env_d and env_d.status == "ok" and env_d.data:
            cats = env_d.data.get("categories", [])
            model_digest["model_d"] = {
                "status": "ok",
                "ood_flagged": env_d.data.get("ood", {}).get("flagged", False),
                "predicted_categories": env_d.data.get("predicted_categories", []),
                "flagged_categories": [
                    {"category": c.get("category"), "prob": c.get("probability"), "evidence": c.get("evidence_sentence")}
                    for c in cats if c.get("predicted")
                ],
            }
        else:
            model_digest["model_d"] = {"status": "unavailable"}

        # 3. Overall Interpretation & Trust
        overall_interp = getattr(report, "interpretation", None)
        if hasattr(overall_interp, "model_dump"):
            overall_interp = overall_interp.model_dump()
        elif not isinstance(overall_interp, dict):
            overall_interp = {"category": "Mixed picture", "summary": "Multi-model evaluation"}

        trust_summary = getattr(report, "trust", {}) if report else {}

        # 4. Prioritized Issues
        evidence_index = getattr(report, "evidence_index", {}) if report else {}
        top_issues, other_obs = IssuePrioritizer.prioritize_issues(
            envelopes=envelopes,
            normalized=normalized,
            evidence_index=evidence_index,
        )

        # 5. Playbook Reference Excerpts
        playbook_excerpts: List[Dict[str, Any]] = []
        for iss in top_issues:
            pb_item = playbook_kb.find_playbook_item(theme=iss.theme, stage=stage)
            if pb_item and pb_item not in playbook_excerpts:
                playbook_excerpts.append({
                    "id": pb_item.get("id"),
                    "theme": pb_item.get("theme"),
                    "title": pb_item.get("title"),
                    "action": pb_item.get("action"),
                    "suggested_steps": pb_item.get("implementation_steps", [])[:4],
                    "suggested_validation": pb_item.get("validation_method"),
                })

        return {
            "evaluation_id": evaluation_id,
            "user_profile": user_profile,
            "model_digest": model_digest,
            "overall_interpretation": overall_interp,
            "trust_summary": {
                "warnings": trust_summary.get("warnings", []),
                "limitations": trust_summary.get("general_limitations", [])[:3],
            },
            "evidence_index": evidence_index,
            "prioritized_issues": [iss.model_dump() for iss in top_issues],
            "other_observations": other_obs,
            "playbook_excerpts": playbook_excerpts,
        }

