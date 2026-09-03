from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from .enums import Decision, HumanDispositionAction

class VersionSnapshot(BaseModel):
    engine_version: str
    policy_version: str
    warning_catalogue_version: str
    legend_version: str
    cv_version: str = "1.0.0"

class DecisionRecord(BaseModel):
    job_id: str
    document_id: str
    index_record_id: Optional[str] = None
    source_file_hash: str
    provider: Optional[str] = None
    utility_type: Optional[str] = None
    decision: Decision
    reason: str
    versions: VersionSnapshot
    evidence_ids: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    human_disposition: Optional[HumanDispositionAction] = None
    reviewer_comment: Optional[str] = None
