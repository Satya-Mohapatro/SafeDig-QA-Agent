from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from .enums import DetectionMethod, GeometryType, Severity

class DetectedCandidate(BaseModel):
    candidate_id: str
    document_id: str
    page_num: int
    warning_code: str
    business_warning_text: str
    severity: Severity
    detection_method: DetectionMethod
    geometry_type: GeometryType = GeometryType.LINE
    coordinates: List[Any] = Field(default_factory=list)
    bbox: List[float] = Field(default_factory=list)
    confidence: float = 1.0
    intersects_aoi: bool = False
    aoi_distance_pt: float = 0.0
    evidence_ids: List[str] = Field(default_factory=list)
