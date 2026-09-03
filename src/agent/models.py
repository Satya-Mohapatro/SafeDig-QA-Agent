from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AdvisorySummary(BaseModel):
    document_id: str
    summary: str
    contradictions_detected: List[str] = Field(default_factory=list)
    recommended_evidence_ids: List[str] = Field(default_factory=list)
    reviewer_guidance: str
    model_name: str = "deterministic_fallback"
    is_fallback: bool = True
    confidence_assessment: Optional[str] = None
    generated_at: Optional[str] = None
