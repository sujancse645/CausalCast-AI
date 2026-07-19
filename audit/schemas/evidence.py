from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class CommandEvidence(BaseModel):
    command: str
    stdout: str
    stderr: str
    returncode: int
    execution_time_ms: float
    timeout_reached: bool = False

class TestResultEvidence(BaseModel):
    test_name: str
    status: str
    duration_ms: float
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None

class CoverageEvidence(BaseModel):
    covered_lines: int
    total_lines: int
    percentage: float
    missing_lines: List[int] = []

class Evidence(BaseModel):
    command_evidence: Optional[CommandEvidence] = None
    test_result_evidence: Optional[TestResultEvidence] = None
    coverage_evidence: Optional[CoverageEvidence] = None
    additional_data: Optional[Dict[str, Any]] = None
