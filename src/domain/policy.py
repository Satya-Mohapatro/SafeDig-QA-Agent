from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from .enums import Decision

class GateCheck(BaseModel):
    gate_name: str
    passed: bool
    reason: str

class PolicyResult(BaseModel):
    document_id: str
    decision: Decision
    reason: str
    gates: Dict[str, GateCheck] = Field(default_factory=dict)
    reconciliation_id: Optional[str] = None
    evidence_package_id: Optional[str] = None
    safe_mode_applied: bool = False
