"""FastAPI Backend Application."""
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.exporter import ReportExporter
from backend.normalization.currency import EXCHANGE_RATES_USD
from backend.normalization.industry import AVAILABLE_INDUSTRIES
from backend.normalization.locations import SUPPORTED_COUNTRIES, US_STATES
from backend.normalization.normalizer import Normalizer
from backend.orchestrator import Orchestrator
from backend.recommendations.engine import RecommendationEngine
from backend.recommender_stub import get_recommendations_stub
from backend.registry import registry
from backend.report_builder import ReportBuilder
from backend.schemas.options import OptionsResponse
from backend.schemas.recommendation import RecommendationResponse
from backend.schemas.report import EvaluationReport, EvaluationStatusResponse
from backend.schemas.submission import (
    ClarificationRequest,
    ClarificationResponse,
    NormalizedSummary,
    SubmissionInput,
    SubmissionResponse,
    ValidateResponse,
)
from backend.storage import storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load registry
    logger.info("Initializing models from manifest...")
    registry.load_all()
    yield
    # Shutdown
    logger.info("Shutting down backend...")

app = FastAPI(
    title="Startup Evaluation API",
    description="Multi-model machine learning pipeline for startup failure risk evaluation.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware (allows Streamlit frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health & Readiness
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "startup-evaluation-backend"}

@app.get("/ready", tags=["Health"])
def readiness_check():
    if not registry.is_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "load_status": registry.load_status}
        )
    return {"status": "ready", "load_status": registry.load_status}

# Metadata Options
@app.get("/v1/meta/options", response_model=OptionsResponse, tags=["Metadata"])
def get_options():
    return OptionsResponse(
        industries=AVAILABLE_INDUSTRIES,
        countries=SUPPORTED_COUNTRIES,
        us_states=US_STATES,
        currencies=list(EXCHANGE_RATES_USD.keys()),
        stages=["idea", "validation", "MVP", "launched", "growing"],
        business_models=["B2B", "B2C", "B2B2C", "SaaS", "Marketplace", "Subscription", "Transactional", "Usage-based", "Hardware", "Other"],
        team_skills=["engineering", "product", "design", "sales and marketing", "operations", "finance", "domain expertise", "legal", "other"],
        founder_experience=["first-time", "prior startup", "prior exit", "domain veteran"],
        investor_types=["venture capital", "angel", "accelerator", "friends and family", "none"],
        funding_rounds_options=["Round A", "Round B", "Round C", "Round D", "none"],
        field_limits={
            "idea_min_chars": 20,
            "idea_max_chars": 4000,
            "problem_max_chars": 1000,
            "customer_max_chars": 500,
            "max_team_size": 500,
        }
    )

# Models Info
@app.get("/v1/models", tags=["Metadata"])
def get_models_catalog():
    return registry.get_models_info()

# Validation & Normalization Endpoint (Powers Review Page)
@app.post("/v1/evaluations/validate", response_model=ValidateResponse, tags=["Evaluations"])
def validate_submission(payload: SubmissionInput):
    normalized, warnings = Normalizer.normalize(payload)

    # Check applicability for each model
    applicability = {}
    for m_id, adapter in registry.adapters.items():
        sub_payload = normalized.get(f"{m_id}_payload", {})
        is_app, reason = adapter.check_applicability(sub_payload)
        applicability[m_id] = {
            "applicable": is_app,
            "reason": reason if not is_app else "Meets input requirements"
        }

    summary = NormalizedSummary(
        idea_description=normalized["idea_description"],
        industry=normalized["industry"],
        country=normalized["country"],
        state=normalized["state"],
        funding_total_usd=normalized["funding_total_usd"],
        funding_rounds=normalized["funding_rounds"],
        exchange_rate_used=normalized["exchange_rate_used"],
        exchange_rate_date=normalized["exchange_rate_date"],
        original_funding=normalized["original_funding"],
        original_currency=normalized["original_currency"],
        stage=normalized["stage"],
        provenance_provided_fields=normalized["provenance"]["provided_fields"],
        provenance_missing_fields=normalized["provenance"]["missing_fields"],
    )

    return ValidateResponse(
        valid=True,
        normalized=summary,
        models_applicability=applicability,
        warnings=warnings
    )

# Background processing worker
def _process_evaluation(eval_id: str, normalized: Dict[str, Any], created_at: str):
    try:
        storage.set_stage(eval_id, "running_models", status="running")
        envelopes = Orchestrator.run_all_models(normalized)

        # Failure handling: If every model failed completely, fail the evaluation cleanly
        all_failed = all(env.status == "error" for env in envelopes.values())
        if all_failed:
            storage.set_failed(eval_id, "All analytical models failed to produce predictions.")
            return

        storage.set_stage(eval_id, "building_report")
        report = ReportBuilder.build_report(eval_id, normalized, envelopes, created_at)
        storage.update_envelopes_and_report(
            eval_id, envelopes, report, status="report_ready", stage="generating_recommendations"
        )

        # Generate prioritized recommendations (LLM with playbook fallback)
        try:
            recs = RecommendationEngine.generate(eval_id, normalized, envelopes, report)
        except Exception as llm_err:
            logger.warning(f"Recommendation generation encountered error: {llm_err}. Using fallback.", exc_info=True)
            recs = RecommendationResponse(
                evaluation_id=eval_id,
                status="complete",
                generation_method="template_playbook",
                is_fallback=True,
                recommendations=[],
            )
        storage.update_recommendations(eval_id, recs, status="complete", stage="complete")
    except Exception as e:
        logger.error(f"Error processing evaluation {eval_id}: {e}", exc_info=True)
        storage.set_failed(eval_id, str(e))

# Evaluation Submission
@app.post("/v1/evaluations", response_model=SubmissionResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Evaluations"])
def submit_evaluation(payload: SubmissionInput, background_tasks: BackgroundTasks):
    if not payload.consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent is required to evaluate submission."
        )

    normalized, warnings = Normalizer.normalize(payload)
    eval_id = f"eval_{uuid.uuid4().hex[:12]}"
    raw_dict = payload.model_dump()
    record = storage.create(eval_id, normalized, raw_submission=raw_dict, consent=payload.consent)

    # Enqueue background task
    background_tasks.add_task(_process_evaluation, eval_id, normalized, record["created_at"])

    return SubmissionResponse(
        evaluation_id=eval_id,
        status="queued",
        created_at=record["created_at"],
        check_status_url=f"/v1/evaluations/{eval_id}"
    )

# Status Check
@app.get("/v1/evaluations/{eval_id}", response_model=EvaluationStatusResponse, tags=["Evaluations"])
def get_evaluation_status(eval_id: str):
    rec = storage.get(eval_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")

    per_model = {}
    envelopes = rec.get("envelopes", {})
    for m_id in ["model_a", "model_b", "model_c", "model_d"]:
        if m_id in envelopes:
            per_model[m_id] = envelopes[m_id].status
        else:
            per_model[m_id] = "pending" if rec["status"] in ("queued", "running") else "unavailable"

    lineage = storage.get_lineage(eval_id)

    return EvaluationStatusResponse(
        evaluation_id=eval_id,
        version=rec.get("version", 1),
        parent_id=rec.get("parent_id"),
        status=rec["status"],
        stage=rec["stage"],
        created_at=rec["created_at"],
        completed_at=rec["completed_at"],
        per_model_status=per_model,
        report_url=f"/v1/evaluations/{eval_id}/report" if rec["status"] in ("report_ready", "complete") else None,
        available_versions=lineage,
    )

# Structured Report
@app.get("/v1/evaluations/{eval_id}/report", response_model=EvaluationReport, tags=["Evaluations"])
def get_evaluation_report(eval_id: str):
    rec = storage.get(eval_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")

    if rec["status"] not in ("report_ready", "complete"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Report is not ready yet (current status: {rec['status']})"
        )

    return rec["report"]

# Prioritized Recommendations Endpoint
@app.get("/v1/evaluations/{eval_id}/recommendations", response_model=RecommendationResponse, tags=["Evaluations"])
def get_evaluation_recommendations(eval_id: str):
    rec = storage.get(eval_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")

    stored_recs = rec.get("recommendations")
    if stored_recs:
        return stored_recs

    # If report is ready but recommendations not yet cached, generate deterministically
    if rec.get("status") in ("report_ready", "complete") and rec.get("report") and rec.get("envelopes"):
        recs = RecommendationEngine.generate(eval_id, rec["normalized"], rec["envelopes"], rec["report"])
        storage.update_recommendations(eval_id, recs)
        return recs

    # Otherwise return empty response while still running
    return RecommendationResponse(
        evaluation_id=eval_id,
        status="running",
        is_fallback=True,
        recommendations=[],
    )

# Clarification Loop: submit answers and create a new linked version
@app.post("/v1/evaluations/{eval_id}/clarifications", response_model=ClarificationResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Evaluations"])
def submit_clarifications(eval_id: str, payload: ClarificationRequest, background_tasks: BackgroundTasks):
    rec = storage.get(eval_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent evaluation not found")

    answers = payload.answers
    if not answers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one clarification answer is required")

    # Construct updated raw submission & pitch
    raw_sub = dict(rec.get("raw_submission", {}))
    clarification_text = "\n\n[Clarifications Provided]:\n" + "\n".join([
        f"- {a.aspect}: {a.answer}" for a in answers if a.answer.strip()
    ])

    orig_desc = raw_sub.get("idea_description") or rec["normalized"].get("idea_description", "")
    raw_sub["idea_description"] = (orig_desc + clarification_text).strip()

    # Update specific fields if the clarification provides details
    for a in answers:
        asp_lower = a.aspect.lower()
        ans_val = a.answer.strip()
        if "target customer" in asp_lower or "customer" in asp_lower:
            raw_sub["target_customer"] = ans_val
        elif "competitor" in asp_lower:
            raw_sub["competitors"] = ans_val
        elif "validation" in asp_lower or "traction" in asp_lower:
            raw_sub["validation_evidence"] = ans_val

    sub_input = SubmissionInput(**raw_sub)
    normalized, _ = Normalizer.normalize(sub_input)

    root_id = rec.get("root_id") or eval_id
    next_version = rec.get("version", 1) + 1
    new_eval_id = f"{root_id}_v{next_version}"

    clarifications_dict = [a.model_dump() for a in answers]
    new_record = storage.create_version(
        parent_id=eval_id,
        new_eval_id=new_eval_id,
        normalized=normalized,
        raw_submission=raw_sub,
        clarifications=clarifications_dict,
    )

    if not new_record:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initialize new version")

    background_tasks.add_task(_process_evaluation, new_eval_id, normalized, new_record["created_at"])

    return ClarificationResponse(
        evaluation_id=new_eval_id,
        parent_id=eval_id,
        version=new_record["version"],
        status="queued",
        created_at=new_record["created_at"],
        check_status_url=f"/v1/evaluations/{new_eval_id}",
    )

# Report Export Endpoint (HTML, JSON, PDF)
@app.get("/v1/evaluations/{eval_id}/export", tags=["Evaluations"])
def export_evaluation(eval_id: str, format: str = Query("json", pattern="^(json|html|pdf)$")):
    rec = storage.get(eval_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")

    report = rec.get("report")
    if not report or rec.get("status") not in ("report_ready", "complete"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Report is not ready for export (current status: {rec.get('status')})"
        )

    recommendations = rec.get("recommendations")

    if format == "json":
        content = ReportExporter.export_json(report, recommendations)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="report_{eval_id}.json"'},
        )
    elif format == "html":
        content = ReportExporter.export_html(report, recommendations)
        return Response(
            content=content,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="report_{eval_id}.html"'},
        )
    elif format == "pdf":
        content = ReportExporter.export_pdf(report, recommendations)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="report_{eval_id}.pdf"'},
        )

# Delete Evaluation (Data Removal)
@app.delete("/v1/evaluations/{eval_id}", tags=["Evaluations"])
def delete_evaluation(eval_id: str):
    success = storage.delete(eval_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return {"deleted": True, "evaluation_id": eval_id}

