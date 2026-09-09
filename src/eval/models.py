from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.domain.enums import Decision, ReconciliationOutcome

class GroundTruthCase(BaseModel):
    case_id: str
    job_id: str
    root_dir: str
    document_id: Optional[str] = None
    filename: Optional[str] = None
    utility_name: str
    expected_decision: Decision
    expected_outcome: ReconciliationOutcome
    expected_hazard_codes: List[str] = Field(default_factory=list)
    is_safety_critical: bool = True
    notes: Optional[str] = None

class CaseEvaluationResult(BaseModel):
    case_id: str
    job_id: str
    document_id: str
    filename: str
    utility_name: str
    expected_decision: str
    actual_decision: str
    expected_outcome: str
    actual_outcome: str
    is_decision_match: bool
    is_outcome_match: bool
    is_escaped_hazard: bool  # True if safety critical hazard was classified as AUTO_CLEAR
    reason: str

class EvaluationMetricResult(BaseModel):
    total_cases: int
    decision_accuracy: float
    outcome_accuracy: float
    precision: float
    recall: float
    f1_score: float
    escaped_hazard_count: int  # Must be 0 for safety signoff
    decision_confusion_matrix: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    outcome_confusion_matrix: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    provider_accuracy: Dict[str, float] = Field(default_factory=dict)

class BenchmarkReport(BaseModel):
    run_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    engine_version: str
    policy_version: str
    total_cases_evaluated: int
    safety_compliance_passed: bool  # True if escaped_hazard_count == 0
    metrics: EvaluationMetricResult
    case_results: List[CaseEvaluationResult] = Field(default_factory=list)
