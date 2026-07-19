from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Metric Definitions
# -----------------------------------------------------------------------------
class MetricDefinitionBase(BaseModel):
    name: str
    description: str | None = None
    category: str = "General"
    unit: str
    currency: str | None = None
    aggregation_type: str
    time_grain: str
    formula: str | None = None
    directionality: str = "higher_is_better"
    dimensions: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)


class MetricDefinitionCreate(MetricDefinitionBase):
    pass


class MetricDefinitionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    unit: str | None = None
    currency: str | None = None
    aggregation_type: str | None = None
    time_grain: str | None = None
    formula: str | None = None
    directionality: str | None = None
    dimensions: list[str] | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)


class MetricDefinitionResponse(MetricDefinitionBase):
    id: str
    version: int
    status: str
    owner: str | None
    tenant_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# KPI Snapshots
# -----------------------------------------------------------------------------
class KPISnapshotBase(BaseModel):
    metric_id: str
    metric_version: int
    period_start: datetime
    period_end: datetime
    grain: str
    actual_value: float | None = None
    forecast_value: float | None = None
    target_value: float | None = None
    variance: float | None = None
    variance_percentage: float | None = None
    confidence: float | None = None
    status: str
    trend: str | None = None
    dimensions: dict[str, Any] = Field(default_factory=dict)
    data_completeness: float | None = None
    model_version: str | None = None


class KPISnapshotResponse(KPISnapshotBase):
    id: str
    tenant_id: str | None
    checksum: str
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# KPI Targets
# -----------------------------------------------------------------------------
class KPITargetBase(BaseModel):
    metric_id: str
    period_start: datetime
    period_end: datetime
    target_type: str
    value: float
    currency: str | None = None


class KPITargetCreate(KPITargetBase):
    pass


class KPITargetResponse(KPITargetBase):
    id: str
    owner: str | None
    status: str
    tenant_id: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Dashboards
# -----------------------------------------------------------------------------
class DashboardWidgetBase(BaseModel):
    title: str
    widget_type: str
    metric_id: str | None = None
    data_source: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)
    filters: dict[str, Any] = Field(default_factory=dict)
    layout: dict[str, Any] = Field(default_factory=dict)


class DashboardWidgetResponse(DashboardWidgetBase):
    id: str
    dashboard_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardBase(BaseModel):
    name: str
    description: str | None = None
    dashboard_type: str = "custom"
    visibility: str = "private"
    layout: dict[str, Any] = Field(default_factory=dict)
    filters: dict[str, Any] = Field(default_factory=dict)
    theme_settings: dict[str, Any] = Field(default_factory=dict)


class DashboardCreate(DashboardBase):
    pass


class DashboardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    visibility: str | None = None
    layout: dict[str, Any] | None = None
    filters: dict[str, Any] | None = None
    theme_settings: dict[str, Any] | None = None
    status: str | None = None


class DashboardResponse(DashboardBase):
    id: str
    owner: str | None
    version: int
    status: str
    tenant_id: str | None
    created_at: datetime
    updated_at: datetime
    widgets: list[DashboardWidgetResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Evaluation Engine
# -----------------------------------------------------------------------------
class KPIEvaluationRequest(BaseModel):
    period_start: datetime
    period_end: datetime
    grain: str
    dimensions: dict[str, Any] = Field(default_factory=dict)
    forecast_scenario_id: str | None = None
    actual_value: float | None = None
    forecast_value: float | None = None
