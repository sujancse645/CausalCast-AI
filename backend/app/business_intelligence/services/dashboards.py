from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.business_intelligence import Dashboard
from app.schemas.business_intelligence import DashboardCreate, DashboardUpdate


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def list_dashboards(self, tenant_id: str | None = None) -> list[Dashboard]:
        stmt = select(Dashboard)
        if tenant_id:
            stmt = stmt.where(Dashboard.tenant_id == tenant_id)
        return list(self.db.execute(stmt).scalars().all())

    def get_dashboard(self, dashboard_id: str) -> Dashboard | None:
        return self.db.execute(select(Dashboard).where(Dashboard.id == dashboard_id)).scalar_one_or_none()

    def create_dashboard(
        self, data: DashboardCreate, tenant_id: str | None = None, owner: str | None = None
    ) -> Dashboard:
        dashboard = Dashboard(
            name=data.name,
            description=data.description,
            dashboard_type=data.dashboard_type,
            visibility=data.visibility,
            layout_json=data.layout,
            filters_json=data.filters,
            theme_settings_json=data.theme_settings,
            tenant_id=tenant_id,
            owner=owner,
        )
        self.db.add(dashboard)
        self.db.commit()
        self.db.refresh(dashboard)
        return dashboard

    def update_dashboard(self, dashboard: Dashboard, data: DashboardUpdate) -> Dashboard:
        for k, v in data.model_dump(exclude_unset=True).items():
            if k == "layout":
                dashboard.layout_json = v
            elif k == "filters":
                dashboard.filters_json = v
            elif k == "theme_settings":
                dashboard.theme_settings_json = v
            else:
                setattr(dashboard, k, v)
        self.db.commit()
        self.db.refresh(dashboard)
        return dashboard
