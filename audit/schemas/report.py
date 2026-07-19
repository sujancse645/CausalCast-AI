from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from .findings import Finding
from .scores import OverallScore

class AuditReport(BaseModel):
    report_id: str
    timestamp: datetime
    project_name: str
    findings: List[Finding] = []
    scores: Optional[OverallScore] = None
    metadata: Optional[Dict[str, Any]] = None
