from typing import Any

class ForecastErrorAnalysisService:
    @staticmethod
    def analyze_error(model_run_id: str, diagnostics: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze forecast errors and link to potential root causes like drift or anomalies.
        """
        causes = []
        severity = "low"
        
        # Simple heuristic mappings based on residual diagnostics
        if diagnostics.get("mean_residual", 0.0) > 10.0:
            causes.append("Significant under-prediction bias detected.")
            severity = "high"
            
        if diagnostics.get("autocorrelation_lag1", 0.0) > 0.5:
            causes.append("High residual autocorrelation suggests missing lagged features or seasonality.")
            severity = "medium"
            
        if not causes:
            causes.append("No obvious root causes identified in standard residuals.")
            
        return {
            "suspected_causes": causes,
            "severity": severity,
            "confidence": 0.6 if severity != "low" else 0.9,
            "recommended_action": "Investigate missing predictors or retrain if drift is confirmed."
        }
