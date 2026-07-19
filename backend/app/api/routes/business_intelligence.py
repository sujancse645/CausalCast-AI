from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.business_intelligence.services.dashboards import DashboardService
from app.core.database import get_db
from app.models.business_intelligence import Dashboard, KPISnapshot, MetricDefinition
from app.schemas.business_intelligence import (
    DashboardCreate,
    DashboardResponse,
    DashboardUpdate,
    KPIEvaluationRequest,
    KPISnapshotResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])
DBSession = Annotated[Session, Depends(get_db)]


@router.get("/dashboards", response_model=list[DashboardResponse])
def get_dashboards(db: DBSession) -> list[Dashboard]:
    """List dashboards."""
    svc = DashboardService(db)
    return svc.list_dashboards()


@router.post("/dashboards", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
def create_dashboard(data: DashboardCreate, db: DBSession) -> Dashboard:
    """Create a new dashboard."""
    svc = DashboardService(db)
    return svc.create_dashboard(data, owner="system")


@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
def get_dashboard(dashboard_id: str, db: DBSession) -> Dashboard:
    """Get dashboard by ID."""
    svc = DashboardService(db)
    dashboard = svc.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.patch("/dashboards/{dashboard_id}", response_model=DashboardResponse)
def update_dashboard(dashboard_id: str, data: DashboardUpdate, db: DBSession) -> Dashboard:
    """Update a dashboard."""
    svc = DashboardService(db)
    dashboard = svc.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return svc.update_dashboard(dashboard, data)


@router.post("/kpis/{metric_id}/evaluate", response_model=KPISnapshotResponse)
def evaluate_kpi(metric_id: str, req: KPIEvaluationRequest, db: DBSession) -> KPISnapshot:
    """
    Evaluate a KPI metric safely using KPIEngine and persist snapshot.
    """
    from app.business_intelligence.core.kpi_engine import KPIEngine

    metric = db.execute(select(MetricDefinition).where(MetricDefinition.id == metric_id)).scalar_one_or_none()

    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")

    engine = KPIEngine(db)
    snapshot = engine.evaluate_metric(metric, req, actual=req.actual_value, forecast=req.forecast_value)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot
