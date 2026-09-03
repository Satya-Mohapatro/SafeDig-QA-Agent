from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from .enums import Severity, GeometryType

class WarningDefinition(BaseModel):
    warning_code: str
    provider: str
    utility_type: str
    business_warning_text: str
    severity: Severity
    geometry_type: GeometryType = GeometryType.LINE
    aoi_required: bool = True
    detection_profile: Optional[str] = None
    version: str = "1.0.0"
    active: bool = True

class ClaimedWarning(BaseModel):
    claimed_warning_id: str
    document_id: str
    index_record_id: Optional[str] = None
    warning_code: Optional[str] = None
    raw_warning_text: str
    severity: Severity = Severity.UNKNOWN
    upstream_confidence: Optional[float] = None
    upstream_model_version: Optional[str] = None
