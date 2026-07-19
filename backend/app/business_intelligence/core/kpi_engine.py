import ast
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.business_intelligence import KPISnapshot, KPITarget, MetricDefinition
from app.schemas.business_intelligence import KPIEvaluationRequest


class KPIEngineError(Exception):
    pass


class KPIEngine:
    """
    Core engine for safe, deterministic KPI evaluation.
    Converts raw actuals, forecasts, and targets into business-ready KPI snapshots.
    """

    # Safe operators for formula evaluation
    BINARY_OPERATORS: dict[type[ast.operator], Callable[[float, float], float]] = {
        ast.Add: lambda left, right: left + right,
        ast.Sub: lambda left, right: left - right,
        ast.Mult: lambda left, right: left * right,
        ast.Div: lambda left, right: left / right,
    }
    UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[float], float]] = {
        ast.USub: lambda value: -value,
    }

    def __init__(self, db: Session):
        self.db = db

    def _safe_eval(self, node: ast.AST, variables: dict[str, float]) -> float:
        """Safely evaluate mathematical expressions."""
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
            return float(node.value)
        elif isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            raise KPIEngineError(f"Undefined variable in formula: {node.id}")
        elif isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left, variables)
            right = self._safe_eval(node.right, variables)
            binary_op = type(node.op)
            if binary_op not in self.BINARY_OPERATORS:
                raise KPIEngineError(f"Unsupported operator: {binary_op}")
            if binary_op == ast.Div and right == 0:
                raise KPIEngineError("Division by zero in KPI formula")
            return self.BINARY_OPERATORS[binary_op](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand, variables)
            unary_op = type(node.op)
            if unary_op not in self.UNARY_OPERATORS:
                raise KPIEngineError(f"Unsupported unary operator: {unary_op}")
            return self.UNARY_OPERATORS[unary_op](operand)
        raise KPIEngineError(f"Unsupported expression node: {type(node)}")

    def evaluate_formula(self, formula: str, variables: dict[str, float]) -> float:
        """Parse and safely evaluate a formula string."""
        if not formula:
            raise KPIEngineError("Formula is empty")
        try:
            tree = ast.parse(formula, mode="eval")
            return self._safe_eval(tree.body, variables)
        except SyntaxError as exc:
            raise KPIEngineError(f"Syntax error in formula: {exc}") from exc

    def _aggregate(self, values: list[float], agg_type: str) -> float:
        """Aggregate a list of values."""
        if not values:
            return 0.0

        valid_values = [v for v in values if v is not None]
        if not valid_values:
            return 0.0

        if agg_type == "sum":
            return sum(valid_values)
        elif agg_type == "average":
            return sum(valid_values) / len(valid_values)
        elif agg_type == "minimum":
            return min(valid_values)
        elif agg_type == "maximum":
            return max(valid_values)
        elif agg_type == "count":
            return len(valid_values)

        raise KPIEngineError(f"Unsupported aggregation type: {agg_type}")

    def compute_variance(
        self, actual: float | None, target_or_forecast: float | None, directionality: str
    ) -> tuple[float | None, float | None, str]:
        """
        Compute absolute and percentage variance, and determine the status based on directionality.
        Status: on_track, watch, critical, exceeded.
        """
        if actual is None or target_or_forecast is None:
            return None, None, "unavailable"

        variance = actual - target_or_forecast

        if target_or_forecast == 0:
            pct_variance = None if variance == 0 else (100.0 if variance > 0 else -100.0)
        else:
            pct_variance = (variance / abs(target_or_forecast)) * 100.0

        status = "on_track"
        if directionality == "higher_is_better":
            if variance < 0:
                status = "critical" if pct_variance and pct_variance < -10 else "watch"
            elif variance > 0:
                status = "exceeded"
        elif directionality == "lower_is_better":
            if variance > 0:
                status = "critical" if pct_variance and pct_variance > 10 else "watch"
            elif variance < 0:
                status = "exceeded"

        return variance, pct_variance, status

    def evaluate_metric(
        self,
        metric: MetricDefinition,
        req: KPIEvaluationRequest,
        actual: float | None = None,
        forecast: float | None = None,
    ) -> KPISnapshot:
        """
        Evaluate a metric definition to produce a snapshot.
        If actual/forecast are not provided, it would theoretically fetch them via Data/Forecast services (stubbed for safety here).
        """
        # Fetch target if it exists
        stmt = (
            select(KPITarget)
            .where(
                KPITarget.metric_id == metric.id,
                KPITarget.period_start <= req.period_start,
                KPITarget.period_end >= req.period_end,
            )
            .limit(1)
        )
        target_obj = self.db.execute(stmt).scalar_one_or_none()
        target_val = target_obj.value if target_obj else None

        # Compare actual vs target (or forecast if no target)
        baseline_for_variance = target_val if target_val is not None else forecast
        variance, variance_pct, status = self.compute_variance(actual, baseline_for_variance, metric.directionality)

        import hashlib
        import json

        checksum_payload = json.dumps(
            {"metric": metric.id, "start": req.period_start.isoformat(), "actual": actual, "forecast": forecast},
            sort_keys=True,
        )
        checksum = hashlib.sha256(checksum_payload.encode("utf-8")).hexdigest()

        snapshot = KPISnapshot(
            metric_id=metric.id,
            metric_version=metric.version,
            period_start=req.period_start,
            period_end=req.period_end,
            grain=req.grain,
            actual_value=actual,
            forecast_value=forecast,
            target_value=target_val,
            variance=variance,
            variance_percentage=variance_pct,
            status=status,
            dimensions_json=req.dimensions,
            data_completeness=1.0 if actual is not None else 0.0,
            checksum=checksum,
        )
        return snapshot
