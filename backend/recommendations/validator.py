"""Output Validator implementing Section 5.9 rules."""
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from backend.schemas.recommendation import (
    ClarifyingQuestion,
    RecommendationItem,
    RecommendationResponse,
)

PROHIBITED_PHRASES = [
    r"\bguarantee\b",
    r"\bguaranteed\b",
    r"\bguarantees\b",
    r"\bwill definitely\b",
    r"\bensure success\b",
    r"\bensures success\b",
    r"\bprevents? failure\b",
    r"\b100% chance\b",
    r"\bzero risk\b",
    r"\bcertain outcome\b",
]


class RecommendationValidator:
    @staticmethod
    def validate(
        raw_text: str,
        grounding_pack: Dict[str, Any],
    ) -> Tuple[bool, List[str], Optional[RecommendationResponse]]:
        """
        Validates LLM output against the JSON schema, assigned issue priorities,
        grounded evidence index, and prohibited claim filters.
        """
        errors: List[str] = []

        # 1. Clean and parse JSON
        cleaned = raw_text.strip()
        # Strip markdown code fences if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[len("```"):].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-len("```")].strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON format: {str(e)}"], None

        if not isinstance(data, dict):
            return False, ["Output root must be a JSON dictionary object."], None

        # Build lookup of assigned issues
        assigned_issues = {
            iss["id"]: iss for iss in grounding_pack.get("prioritized_issues", [])
        }
        known_evidence_ids = set(grounding_pack.get("evidence_index", {}).keys())

        raw_recs = data.get("recommendations", [])
        if not isinstance(raw_recs, list) or len(raw_recs) == 0:
            errors.append("Output must contain a non-empty 'recommendations' array.")

        validated_items: List[RecommendationItem] = []

        for idx, item in enumerate(raw_recs):
            loc = f"recommendations[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{loc} must be an object.")
                continue

            issue_id = item.get("issue_id")
            if not issue_id or issue_id not in assigned_issues:
                errors.append(
                    f"{loc}.issue_id '{issue_id}' does not match any assigned issue ID from the grounding pack."
                )
                continue

            expected_prio = assigned_issues[issue_id].get("priority")
            actual_prio = item.get("priority")

            # Check Rule 4: Priority must strictly equal assigned priority
            if actual_prio != expected_prio:
                errors.append(
                    f"{loc} priority '{actual_prio}' does not match assigned issue priority '{expected_prio}' for issue '{issue_id}'."
                )

            # Check 7 required fields non-empty
            req_str_fields = [
                "identified_problem_or_risk",
                "why_it_matters_for_this_startup",
                "specific_action",
                "expected_benefit",
                "validation_method",
            ]
            for f in req_str_fields:
                val = item.get(f)
                if not val or not isinstance(val, str) or len(val.strip()) < 5:
                    errors.append(f"{loc}.{f} must be a non-empty string with adequate detail.")

            # Check implementation steps
            steps = item.get("implementation_steps")
            if not isinstance(steps, list) or len(steps) < 3:
                errors.append(f"{loc}.implementation_steps must contain at least 3 concrete steps.")

            # Check Rule 3: Every cited evidence reference must exist in the grounding pack
            for ev_ref in item.get("evidence_refs", []):
                if known_evidence_ids and ev_ref not in known_evidence_ids:
                    errors.append(
                        f"{loc}.evidence_refs citation '{ev_ref}' not found in grounding pack evidence index."
                    )

            # Check prohibited phrases across narrative fields
            full_text = " ".join([
                str(item.get("why_it_matters_for_this_startup", "")),
                str(item.get("specific_action", "")),
                str(item.get("expected_benefit", "")),
                str(item.get("validation_method", "")),
            ])
            for pat in PROHIBITED_PHRASES:
                if re.search(pat, full_text, flags=re.IGNORECASE):
                    errors.append(
                        f"{loc} contains prohibited claim or guarantee pattern: '{pat}'."
                    )

            try:
                rec_obj = RecommendationItem(
                    id=str(item.get("id") or f"rec_{idx + 1}"),
                    issue_id=str(issue_id),
                    identified_problem_or_risk=str(item.get("identified_problem_or_risk", "")),
                    why_it_matters_for_this_startup=str(item.get("why_it_matters_for_this_startup", "")),
                    specific_action=str(item.get("specific_action", "")),
                    priority=expected_prio,  # ensure exact fidelity
                    implementation_steps=[str(s) for s in (steps or [])],
                    expected_benefit=str(item.get("expected_benefit", "")),
                    validation_method=str(item.get("validation_method", "")),
                    evidence_refs=[str(r) for r in item.get("evidence_refs", [])],
                    playbook_refs=[str(p) for p in item.get("playbook_refs", [])],
                    assumptions=[str(a) for a in item.get("assumptions", [])],
                )
                validated_items.append(rec_obj)
            except Exception as e:
                errors.append(f"{loc} schema instantiation error: {str(e)}")

        # Parse clarifying questions
        questions: List[ClarifyingQuestion] = []
        for q in data.get("clarifying_questions", []):
            if isinstance(q, dict) and q.get("question"):
                questions.append(
                    ClarifyingQuestion(
                        question=str(q.get("question")),
                        aspect=str(q.get("aspect", "Context")),
                        reason_it_matters=str(q.get("reason_it_matters", "")),
                    )
                )

        # Parse general assumptions
        assumptions = [str(a) for a in data.get("assumptions", []) if isinstance(a, str)]

        if errors:
            return False, errors, None

        resp = RecommendationResponse(
            evaluation_id=grounding_pack.get("evaluation_id", "eval_unknown"),
            status="complete",
            generation_method="llm_direct",
            is_fallback=False,
            recommendations=validated_items,
            other_observations=grounding_pack.get("other_observations", []),
            clarifying_questions=questions,
            assumptions=assumptions,
        )
        return True, [], resp

