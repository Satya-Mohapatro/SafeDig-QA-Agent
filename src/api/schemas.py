from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from src.domain.enums import Decision, HumanDispositionAction, ReconciliationOutcome

class JobSubmitRequest(BaseModel):
    root_dir: str
    job_id: Optional[str] = None
    output_dir: Optional[str] = None

class JobSubmitResponse(BaseModel):
    job_id: str
    status: str
    message: str
    overall_decision: str
    total_documents_processed: int
    reports: Dict[str, str] = Field(default_factory=dict)

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    overall_decision: str
    total_records: int
    auto_clear_count: int
    human_review_count: int
    blocked_count: int
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    reports: Dict[str, str] = Field(default_factory=dict)

class QAQueueItem(BaseModel):
    job_id: str
    index_record_id: str
    document_id: str
    filename: str
    utility_name: str
    utility_type: str
    upstream_claim: Optional[str] = None
    independent_findings_count: int
    reconciliation_outcome: str
    decision: str
    reason: str
    evidence_package_id: str
    evidence_count: int
    advisory_summary: Optional[str] = None

class QAQueueListResponse(BaseModel):
    total_items: int
    items: List[QAQueueItem]

class ReviewWorkspacePayload(BaseModel):
    job_id: str
    document_id: str
    index_record_id: str
    filename: str
    utility_name: str
    utility_type: str
    
    # 1. Map details
    page_count: int
    modality: str
    pdf_path: str
    
    # 2. AOI details
    aoi_method: str
    aoi_confidence: float
    aoi_bbox: Optional[List[float]] = None
    aoi_coordinates: List[Any] = Field(default_factory=list)
    
    # 3. Reconciliation & Findings
    reconciliation_outcome: str
    upstream_claim: Optional[str] = None
    independent_findings: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 4. Legend profile
    legend_id: Optional[str] = None
    legend_features: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 5. Evidence package
    evidence_package_id: str
    evidence_items: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 6. Advisory briefing
    advisory: Optional[Dict[str, Any]] = None
    
    # 7. Policy gate checks
    decision: str
    reason: str
    gates: Dict[str, Any] = Field(default_factory=dict)

class HumanDispositionRequest(BaseModel):
    job_id: str
    document_id: str
    index_record_id: str
    action: HumanDispositionAction
    reviewer_id: str
    reviewer_comment: str

class HumanDispositionResponse(BaseModel):
    job_id: str
    document_id: str
    previous_decision: str
    new_decision: str
    action: HumanDispositionAction
    reviewer_id: str
    reviewer_comment: str
    timestamp: str
    audit_persisted: bool = True
