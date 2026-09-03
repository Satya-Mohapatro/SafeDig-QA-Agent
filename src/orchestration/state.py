from typing import TypedDict, List, Dict, Any, Optional
from src.domain.enums import Decision

class MapQAState(TypedDict, total=False):
    job_id: str
    workflow_run_id: str
    root_dir: str
    output_dir: str
    
    # Ingestion & Index
    manifest: Dict[str, Any]
    discovered_files: List[Dict[str, Any]]
    index_records: List[Dict[str, Any]]
    resolved_documents: Dict[str, Any]
    validation_report: Dict[str, Any]
    accounting_report: Dict[str, Any]
    
    # Processed Results & Artifacts
    document_results: List[Dict[str, Any]]
    evidence_packages: Dict[str, Any]
    policy_results: Dict[str, Any]
    
    # Routing & Human-in-the-loop
    overall_decision: str
    human_review_queue: List[Dict[str, Any]]
    advisories: Dict[str, Any]
    human_dispositions: List[Dict[str, Any]]
    decision_records: List[Dict[str, Any]]
    
    # Status & Audit
    status: str
    error_state: Optional[Dict[str, Any]]
    reports: Dict[str, Any]
