import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from app.explainability.core.engine import ExplainabilityEngine
from app.models.explainability import Explanation
from app.models.forecasting import ForecastModelRun


class ExplanationService:
    @staticmethod
    def get_capabilities(db: Session, model_run_id: str) -> dict[str, Any]:
        run = db.query(ForecastModelRun).filter(ForecastModelRun.id == model_run_id).first()
        if not run:
            return {"supported": False, "reason": "model_not_found", "methods": []}
        return ExplainabilityEngine.get_capabilities(run)

    @staticmethod
    def _generate_cache_key(model_run_id: str, explanation_type: str, method: str, parameters: dict[str, Any]) -> str:
        payload = {
            "run_id": model_run_id,
            "type": explanation_type,
            "method": method,
            "params": parameters
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def create_explanation(
        db: Session,
        model_run_id: str,
        explanation_type: str,
        method: str,
        parameters: dict[str, Any],
        actor_id: str | None = None,
        tenant_id: str | None = None,
        force_refresh: bool = False
    ) -> Explanation:
        
        run = db.query(ForecastModelRun).filter(ForecastModelRun.id == model_run_id).first()
        if not run:
            raise ValueError(f"Model run {model_run_id} not found.")

        # Check cache if not forcing refresh
        if not force_refresh:
            # We could do a more thorough check in the DB matching parameters_json
            # For simplicity, we assume exact match queries
            existing = db.query(Explanation).filter(
                Explanation.model_run_id == model_run_id,
                Explanation.explanation_type == explanation_type,
                Explanation.method == method
            ).all()
            for exp in existing:
                if exp.parameters_json == parameters and exp.status == "completed":
                    return exp

        # Otherwise, instantiate the adapter
        adapter = ExplainabilityEngine.get_adapter(run)
        
        # In a real async flow, we would save the explanation as "pending" and dispatch a Celery job.
        # For lightweight local execution (and synchronous testing), we execute directly.
        try:
            if explanation_type == "global_feature_importance":
                result = adapter.explain_global(method, parameters)
            elif explanation_type == "local_feature_attribution":
                prediction_id = parameters.get("prediction_id", "")
                result = adapter.explain_local(prediction_id, method, parameters)
            else:
                raise ValueError(f"Unsupported explanation type: {explanation_type}")

            explanation = Explanation(
                explanation_type=explanation_type,
                model_run_id=model_run_id,
                method=method,
                method_version="1.0",
                parameters_json=parameters,
                status="completed",
                actor_id=actor_id,
                tenant_id=tenant_id,
                reliability_score=result.get("reliability_score", 1.0),
                warnings_json=result.get("warnings", []),
                limitations_json=result.get("limitations", [])
            )
            # In production, large results would be stored in artifact_storage_key
            # Here we might store a subset or save it properly
            
            db.add(explanation)
            db.commit()
            db.refresh(explanation)
            return explanation

        except Exception as e:
            explanation = Explanation(
                explanation_type=explanation_type,
                model_run_id=model_run_id,
                method=method,
                method_version="1.0",
                parameters_json=parameters,
                status="failed",
                actor_id=actor_id,
                tenant_id=tenant_id,
                warnings_json=[str(e)]
            )
            db.add(explanation)
            db.commit()
            db.refresh(explanation)
            raise e
