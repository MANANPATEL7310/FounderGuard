"""Template-based recommendation generator fulfilling Section 5.8 and 5.10."""
from typing import Any, Dict, List
from backend.recommendations.playbook import playbook_kb
from backend.recommendations.prioritizer import IssuePrioritizer
from backend.schemas.envelope import ModelEnvelope
from backend.schemas.recommendation import (
    ClarifyingQuestion,
    PrioritizedIssue,
    RecommendationItem,
    RecommendationResponse,
)


class RecommendationEngine:
    @staticmethod
    def generate(
        evaluation_id: str,
        normalized: Dict[str, Any],
        envelopes: Dict[str, ModelEnvelope],
        report: Any = None,
    ) -> RecommendationResponse:
        """
        Generates prioritized template recommendations from the curated playbook
        based on deterministically prioritized multi-model issues.
        """
        stage = normalized.get("stage", "idea")
        industry = normalized.get("industry", "Technology")
        idea = normalized.get("idea_description", "your startup")

        # 1. Prioritize issues deterministically
        evidence_index = getattr(report, "evidence_index", {}) if report else {}
        top_issues, other_obs = IssuePrioritizer.prioritize_issues(
            envelopes=envelopes,
            normalized=normalized,
            evidence_index=evidence_index,
        )

        recommendations: List[RecommendationItem] = []
        clarifying_questions: List[ClarifyingQuestion] = []
        overall_assumptions: List[str] = [
            f"Recommendations assume operational stage '{stage}' in {industry}.",
            "All recommendations are reference methodologies from the playbook and must be adapted to your market.",
            "Execution of these steps does not guarantee commercial success or prevent market risks.",
        ]

        # 2. Extract Clarifying Questions from Model C and unstated fields
        env_c = envelopes.get("model_c")
        if env_c and env_c.status == "ok" and env_c.data:
            c_questions = env_c.data.get("missing_information_questions", [])
            for q in c_questions[:4]:
                clarifying_questions.append(
                    ClarifyingQuestion(
                        question=q.get("question", ""),
                        aspect=q.get("aspect", "Business Aspect"),
                        reason_it_matters="Clarifying this aspect provides critical context for refining risk mitigation strategies.",
                    )
                )

        # 3. For each top issue, match playbook chunk and fill recommendation schema
        for idx, issue in enumerate(top_issues):
            rec_id = f"rec_{idx + 1}"
            pb_item = playbook_kb.find_playbook_item(theme=issue.theme, stage=stage)

            # Build tailored 'why it matters' narrative
            quote_snip = f" (Evidence noted: '{issue.evidence_quotes[0][:80]}...')" if issue.evidence_quotes else ""
            if issue.is_gap_only:
                why_it_matters = (
                    f"As a {industry} startup at '{stage}' stage, the pitch currently does not clearly state details regarding "
                    f"{issue.title.lower()}{quote_snip}. Addressing this uncertainty is essential to validate core assumptions."
                )
            else:
                why_it_matters = (
                    f"Analytical models identified {issue.title.lower()} as a key risk theme{quote_snip}. "
                    f"In historical startup cohorts, failure to address this friction point significantly increased mortality."
                )

            if pb_item:
                action = pb_item.get("action", f"Establish clear milestones and validation tests for {issue.title}.")
                steps = pb_item.get("implementation_steps", [
                    f"Define baseline assumptions for {issue.title}.",
                    "Engage prospective buyers or stakeholders to evaluate friction.",
                    "Review metrics and adjust positioning accordingly.",
                ])
                benefit = pb_item.get("expected_benefit", "Reduces operational and market uncertainty.")
                val_method = pb_item.get("validation_method", "Measure milestone completion within 30 days.")
                pb_refs = [pb_item.get("id")]
                item_assumptions = pb_item.get("assumptions", [])
            else:
                action = f"Run structured validation tests focused on {issue.title}."
                steps = [
                    f"Document explicit hypotheses regarding {issue.title}.",
                    "Design a 14-day discovery sprint to test these assumptions with target users.",
                    "Synthesize results and determine go/no-go milestones.",
                ]
                benefit = "Clarifies customer intent and reduces risk."
                val_method = "Complete 10 discovery touchpoints within 14 days."
                pb_refs = ["pb_general_discovery"]
                item_assumptions = ["Team has bandwidth to execute validation tests."]

            rec_item = RecommendationItem(
                id=rec_id,
                issue_id=issue.id,
                identified_problem_or_risk=issue.title,
                why_it_matters_for_this_startup=why_it_matters,
                specific_action=action,
                priority=issue.priority,  # MUST equal assigned issue priority
                implementation_steps=steps,
                expected_benefit=benefit,
                validation_method=val_method,
                evidence_refs=issue.evidence_refs,
                playbook_refs=pb_refs,
                assumptions=item_assumptions,
            )
            recommendations.append(rec_item)

        return RecommendationResponse(
            evaluation_id=evaluation_id,
            status="complete",
            generation_method="template_playbook",
            is_fallback=True,
            recommendations=recommendations,
            other_observations=other_obs,
            clarifying_questions=clarifying_questions,
            assumptions=overall_assumptions,
        )
