from datetime import datetime, UTC
import hashlib
import json
import logging
from typing import Any, Dict

logger = logging.getLogger("audit")

class AuditEvent:
    def __init__(self, action: str, actor_id: str, tenant_id: str, resource: str, details: Dict[str, Any], previous_hash: str = ""):
        self.timestamp = datetime.now(UTC).isoformat()
        self.action = action
        self.actor_id = actor_id
        self.tenant_id = tenant_id
        self.resource = resource
        self.details = details
        self.previous_hash = previous_hash
        self.hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        payload = {
            "timestamp": self.timestamp,
            "action": self.action,
            "actor_id": self.actor_id,
            "tenant_id": self.tenant_id,
            "resource": self.resource,
            "details": self.details,
            "previous_hash": self.previous_hash
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def log(self):
        # In a real system, this would append to a cryptographically verifiable ledger
        # and trigger security events/incidents if thresholds are met.
        logger.info("AUDIT_EVENT", extra={"audit": self.__dict__})

def log_audit_event(action: str, actor_id: str, tenant_id: str, resource: str, details: Dict[str, Any]):
    event = AuditEvent(action, actor_id, tenant_id, resource, details)
    event.log()

def log_security_incident(severity: str, description: str, context: Dict[str, Any]):
    logger.warning("SECURITY_INCIDENT", extra={"severity": severity, "description": description, "context": context})
