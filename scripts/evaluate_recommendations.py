"""Offline evaluation script for recommendations over the 15 golden cases.
Fulfills Section 5.12: checks groundedness, specificity, priority consistency,
and absence of prohibited guarantees.
"""
import json
import logging
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import Any, Dict, List

from backend.adapters.model_a_adapter import ModelAAdapter
from backend.adapters.model_b_adapter import ModelBAdapter
from backend.adapters.model_c_adapter import ModelCAdapter
from backend.adapters.model_d_adapter import ModelDAdapter
from backend.config import ROOT_DIR
from backend.normalization.normalizer import Normalizer
from backend.schemas.submission import SubmissionInput
from backend.recommendations.engine import RecommendationEngine
from tests.test_golden_set import GOLDEN_CASES
from backend.recommendations.grounding import GroundingPackBuilder
from backend.recommendations.prioritizer import IssuePrioritizer
from backend.recommendations.validator import RecommendationValidator
from backend.report_builder import ReportBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluator")


def load_adapters(root: Path) -> Dict[str, Any]:
    adapters = {
        "model_a": ModelAAdapter(),
        "model_b": ModelBAdapter(),
        "model_c": ModelCAdapter(),
        "model_d": ModelDAdapter(),
    }
    adapters["model_a"].load(root / "models/model_a/v1")
    adapters["model_b"].load(root / "models/model_b/v1")
    adapters["model_c"].load(root / "models/model_c/v1")
    adapters["model_d"].load(root / "models/model_d/v1")
    return adapters


def run_evaluation() -> Dict[str, Any]:
    cases = GOLDEN_CASES

    adapters = load_adapters(ROOT_DIR)

    total_cases = len(cases)
    passed_validation = 0
    passed_grounding = 0
    passed_priority = 0
    passed_no_prohibited = 0
    generation_methods: Dict[str, int] = {}
    sample_outputs: List[Dict[str, Any]] = []

    print(f"\n=======================================================")
    print(f"Evaluating Recommendations over {total_cases} Golden Cases")
    print(f"=======================================================\n")

    for idx, case in enumerate(cases):
        case_id = str(case.get("id") or f"case_{idx+1}")
        payload = case.get("input", {})

        # 1. Normalize
        sub_obj = SubmissionInput.model_validate(payload)
        normalized, _ = Normalizer.normalize(sub_obj)

        # 2. Predict with adapters
        envelopes = {}
        for m_id, adapter in adapters.items():
            envelopes[m_id] = adapter.predict(normalized)

        # 3. Build core report (sections 1 to 8)
        report = ReportBuilder.build_report(
            evaluation_id=case_id,
            normalized=normalized,
            envelopes=envelopes,
            created_at="2026-10-29T00:00:00Z",
        )

        # 4. Generate recommendations
        rec_resp = RecommendationEngine.generate(
            evaluation_id=case_id,
            normalized=normalized,
            envelopes=envelopes,
            report=report,
        )

        # 5. Extract grounding pack
        evidence_index = getattr(report, "evidence_index", {})
        top_issues, other_obs = IssuePrioritizer.prioritize_issues(
            envelopes=envelopes,
            normalized=normalized,
            evidence_index=evidence_index,
        )
        grounding_pack = GroundingPackBuilder.build_grounding_pack(
            evaluation_id=case_id,
            normalized=normalized,
            envelopes=envelopes,
            report=report,
        )

        # 6. Validate
        # Check priority consistency
        priorities_match = True
        assigned_priorities = {issue.id: issue.priority for issue in top_issues}
        for rec in rec_resp.recommendations:
            if rec.issue_id in assigned_priorities:
                if rec.priority != assigned_priorities[rec.issue_id]:
                    priorities_match = False
                    break
        if priorities_match:
            passed_priority += 1

        # Check evidence grounding (all cited evidence refs exist)
        grounding_ok = True
        ev_keys = set(evidence_index.keys())
        for rec in rec_resp.recommendations:
            for ref in rec.evidence_refs:
                if ref not in ev_keys:
                    grounding_ok = False
                    break
        if grounding_ok:
            passed_grounding += 1

        # Check prohibited phrases
        prohibited_phrases = ["guarantee", "will definitely", "100% chance", "promise success", "zero risk"]
        no_prohibited = True
        for rec in rec_resp.recommendations:
            combined_text = f"{rec.identified_problem_or_risk} {rec.why_it_matters_for_this_startup} {rec.specific_action} {rec.expected_benefit}".lower()
            for ph in prohibited_phrases:
                if ph in combined_text:
                    no_prohibited = False
                    break
        if no_prohibited:
            passed_no_prohibited += 1

        # Check schema completeness
        schema_ok = len(rec_resp.recommendations) > 0 and all(
            bool(r.id and r.issue_id and r.identified_problem_or_risk and r.specific_action and r.priority and len(r.implementation_steps) >= 3 and r.expected_benefit and r.validation_method)
            for r in rec_resp.recommendations
        )
        if schema_ok and priorities_match and grounding_ok and no_prohibited:
            passed_validation += 1

        gen_m = rec_resp.generation_method
        generation_methods[gen_m] = generation_methods.get(gen_m, 0) + 1

        if idx < 10:
            sample_outputs.append({
                "case_id": case_id,
                "startup_name": normalized.get("startup_name", "N/A"),
                "industry": normalized.get("industry", "N/A"),
                "stage": normalized.get("stage", "N/A"),
                "generation_method": rec_resp.generation_method,
                "is_fallback": rec_resp.is_fallback,
                "issues_count": len(top_issues),
                "recommendations_count": len(rec_resp.recommendations),
                "clarifying_questions_count": len(rec_resp.clarifying_questions),
                "recommendations": [r.model_dump() for r in rec_resp.recommendations[:2]],
                "clarifying_questions": [q.model_dump() for q in rec_resp.clarifying_questions[:2]],
            })

        print(f"[{idx+1:02d}/{total_cases:02d}] {case_id:<45} | method: {gen_m:<18} | recs: {len(rec_resp.recommendations)} | valid: {schema_ok}")

    # Write evaluation markdown report
    report_md = f"""# Recommendation Evaluation Report (Section 5.12)

**Evaluated on:** 15 Golden Submissions  
**Target:** Verify Schema Validation, Groundedness, Priority Consistency, and Prohibited Phrase Filtering.

## Summary Metrics
- **Total Golden Cases:** {total_cases}
- **Validation Pass Rate:** {passed_validation}/{total_cases} ({passed_validation/total_cases*100:.1f}%)
- **Grounding Citation Pass Rate:** {passed_grounding}/{total_cases} ({passed_grounding/total_cases*100:.1f}%)
- **Priority Consistency Rate:** {passed_priority}/{total_cases} ({passed_priority/total_cases*100:.1f}%)
- **Absence of Prohibited Guarantees:** {passed_no_prohibited}/{total_cases} ({passed_no_prohibited/total_cases*100:.1f}%)
- **Generation Method Breakdown:**
"""
    for m, c in generation_methods.items():
        report_md += f"  - `{m}`: {c} cases\n"

    report_md += "\n## Sample Outputs (10 Cases for Human Inspection)\n\n"
    for s in sample_outputs:
        report_md += f"### Case: `{s['case_id']}` ({s['startup_name']} - {s['industry']}, {s['stage']})\n"
        report_md += f"- **Method:** `{s['generation_method']}` (fallback: {s['is_fallback']})\n"
        report_md += f"- **Recommendations Count:** {s['recommendations_count']}\n"
        for r in s['recommendations']:
            report_md += f"  - **[{r['priority'].upper()}] {r['identified_problem_or_risk']}**\n"
            report_md += f"    - *Action:* {r['specific_action']}\n"
            report_md += f"    - *Validation Method:* {r['validation_method']}\n"
            report_md += f"    - *Steps:* {'; '.join(r['implementation_steps'][:3])}\n"
        if s['clarifying_questions']:
            report_md += f"- **Clarifying Questions:**\n"
            for q in s['clarifying_questions']:
                report_md += f"  - *{q['aspect']}:* {q['question']}\n"
        report_md += "\n---\n"

    out_path = ROOT_DIR / "docs/recommendation_evaluation_report.md"
    out_path.write_text(report_md, encoding="utf-8")
    print(f"\nWritten evaluation report with 10 sample outputs to {out_path}")

    return {
        "total": total_cases,
        "passed_validation": passed_validation,
        "methods": generation_methods,
    }


if __name__ == "__main__":
    run_evaluation()
