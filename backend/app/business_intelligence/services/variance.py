from typing import Any

from sqlalchemy.orm import Session


class VarianceAnalysisService:
    """
    Computes variance between Forecast and Actuals securely, preventing hallucination.
    Reuses existing metrics where possible.
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_variance(self, actuals: list[float], forecasts: list[float]) -> dict[str, Any]:
        """Calculate overall variance, MAE, RMSE, and Bias."""
        if not actuals or not forecasts or len(actuals) != len(forecasts):
            return {"error": "Mismatched or empty data arrays", "variance": None}

        valid_pairs = [(a, f) for a, f in zip(actuals, forecasts, strict=True) if a is not None and f is not None]
        if not valid_pairs:
            return {"error": "No valid data pairs", "variance": None}

        total_variance = 0.0
        sum_abs_error = 0.0
        sum_sq_error = 0.0
        bias = 0.0

        for a, f in valid_pairs:
            error = f - a
            total_variance += error
            sum_abs_error += abs(error)
            sum_sq_error += error**2
            bias += error

        n = len(valid_pairs)
        mae = sum_abs_error / n
        rmse = (sum_sq_error / n) ** 0.5
        bias = bias / n

        return {"total_variance": total_variance, "mae": mae, "rmse": rmse, "bias": bias, "data_points": n}
