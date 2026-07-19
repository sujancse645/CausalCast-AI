import logging
from datetime import UTC, datetime

from pydantic import BaseModel

logger = logging.getLogger("cost_attribution")


class ResourceUsage(BaseModel):
    tenant_id: str
    user_id: str
    resource_type: str  # compute, storage, api
    resource_name: str
    units: float  # seconds, GB, requests
    timestamp: str


class CostAttributionService:
    def log_usage(self, tenant_id: str, user_id: str, resource_type: str, resource_name: str, units: float) -> None:
        usage = ResourceUsage(
            tenant_id=tenant_id,
            user_id=user_id,
            resource_type=resource_type,
            resource_name=resource_name,
            units=units,
            timestamp=datetime.now(UTC).isoformat(),
        )
        # Log to billing/cost attribution system
        logger.info("RESOURCE_USAGE", extra={"usage": usage.model_dump()})

    def generate_billing_export(self, tenant_id: str, start_date: str, end_date: str) -> dict[str, str]:
        # Implementation for generating billing export (e.g. CSV for AWS CUR or internal billing)
        return {"status": "export_queued", "tenant_id": tenant_id}


cost_attribution_service = CostAttributionService()
