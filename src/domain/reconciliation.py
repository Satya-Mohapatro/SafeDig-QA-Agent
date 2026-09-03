from pydantic import BaseModel, Field
from typing import List, Optional
from .enums import ReconciliationOutcome, Severity
from .detection import DetectedCandidate
from .warning import ClaimedWarning

class ReconciliationResult(BaseModel):
    reconciliation_id: str
    document_id: str
    claimed_warning: Optional[ClaimedWarning] = None
    detected_candidates: List[DetectedCandidate] = Field(default_factory=list)
    outcome: ReconciliationOutcome
    severity: Severity = Severity.UNKNOWN
    explanation: str
    evidence_ids: List[str] = Field(default_factory=list)
