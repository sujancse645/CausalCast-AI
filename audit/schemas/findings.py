from pydantic import BaseModel
from typing import Optional

from .evidence import Evidence

class Finding(BaseModel):
    id: str
    title: str
    category: str
    severity: str
    confidence: float
    status: str
    evidence: Optional[Evidence] = None
    file: Optional[str] = None
    line: Optional[int] = None
    command: Optional[str] = None
    impact: Optional[str] = None
    reproduction: Optional[str] = None
    recommendation: Optional[str] = None
    estimated_effort: Optional[str] = None
    dependency: Optional[str] = None
    release_blocking: bool = False
