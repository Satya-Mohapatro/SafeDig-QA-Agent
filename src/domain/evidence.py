from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class EvidenceItem(BaseModel):
    evidence_id: str  # Format: E-000001
    document_id: str
    page_num: int
    evidence_type: str  # MAP_CROP, LEGEND_CROP, VECTOR_PATH, OCR_TEXT, SPATIAL_INTERSECTION
    description: str
    data: Dict[str, Any] = Field(default_factory=dict)
    crop_image_path: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class EvidencePackage(BaseModel):
    package_id: str
    document_id: str
    items: List[EvidenceItem] = Field(default_factory=list)
    is_complete: bool = False
    completeness_reasons: List[str] = Field(default_factory=list)
