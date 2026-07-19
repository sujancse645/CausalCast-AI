from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.explainability.services.explanation import ExplanationService
from app.models.explainability import DiagnosticReport, Explanation, Scenario
from app.schemas.explainability import (
    CapabilitiesResponse,
    ExplainabilitySummaryResponse,
    ExplanationRequest,
    ExplanationResponse,
)

router = APIRouter(prefix="/explainability", tags=["explainability"])


@router.get("/summary", response_model=ExplainabilitySummaryResponse)
def get_explainability_summary(db: Session = Depends(get_db)) -> ExplainabilitySummaryResponse:
    global_count = db.scalar(
        select(func.count()).select_from(Explanation).where(Explanation.explanation_type.like("global_%"))
    )
    local_shap_count = db.scalar(
        select(func.count())
        .select_from(Explanation)
        .where(Explanation.explanation_type == "local_feature_attribution")
    )
    anomaly_count = db.scalar(
        select(func.count()).select_from(DiagnosticReport).where(DiagnosticReport.report_type == "anomaly")
    )
    active_scenario_count = db.scalar(
        select(func.count()).select_from(Scenario).where(Scenario.status.in_(("draft", "running")))
    )
    return ExplainabilitySummaryResponse(
        global_explanations_count=global_count or 0,
        local_shap_runs=local_shap_count or 0,
        detected_anomalies=anomaly_count or 0,
        active_scenarios=active_scenario_count or 0,
    )


@router.get(
    "/models/{model_run_id}/capabilities",
    response_model=CapabilitiesResponse,
)
def get_model_capabilities(model_run_id: str, db: Session = Depends(get_db)) -> CapabilitiesResponse:
    """
    Get explainability capabilities for a specific model run.
    """
    capabilities = ExplanationService.get_capabilities(db, model_run_id)
    if capabilities.get("reason") == "model_not_found":
        raise HTTPException(status_code=404, detail="Model run not found")
    return CapabilitiesResponse(**capabilities)


@router.post(
    "/models/{model_run_id}/explain",
    response_model=ExplanationResponse,
)
def explain_model(
    model_run_id: str,
    request: ExplanationRequest,
    db: Session = Depends(get_db),
    # Optional dependency for actor_id / tenant_id if using full auth
) -> ExplanationResponse:
    """
    Generate an explanation for a model or a specific prediction.
    """
    try:
        explanation = ExplanationService.create_explanation(
            db=db,
            model_run_id=model_run_id,
            explanation_type=request.explanation_type,
            method=request.method,
            parameters=request.parameters,
            force_refresh=request.force_refresh,
            actor_id="system",  # placeholder for actual actor
            tenant_id="default",  # placeholder for actual tenant
        )

        # Simulate loading data if it was calculated synchronously
        # In a real async job setup, we'd return a 202 Accepted and a job ID
        data = None
        if explanation.status == "completed":
            # Just mock returning the parameters or a basic structure for now
            data = {"message": f"Explanation generated via {explanation.method}"}

        return ExplanationResponse(
            id=explanation.id,
            explanation_type=explanation.explanation_type,
            model_run_id=explanation.model_run_id,
            prediction_id=explanation.prediction_id,
            method=explanation.method,
            method_version=explanation.method_version,
            status=explanation.status,
            reliability_score=explanation.reliability_score,
            warnings=explanation.warnings_json,
            limitations=explanation.limitations_json,
            runtime_ms=explanation.runtime_ms,
            created_at=explanation.created_at,
            data=data,
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to generate explanation") from exc
