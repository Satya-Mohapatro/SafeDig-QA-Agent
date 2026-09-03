from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from .enums import AOIDetectionMethod, GeometryType

class AOI(BaseModel):
    aoi_id: str
    document_id: str
    page_num: int
    geometry_type: GeometryType = GeometryType.POLYGON
    method: AOIDetectionMethod
    coordinates: List[Any] = Field(default_factory=list)  # (x, y) points in PDF coordinate space
    bbox: Optional[List[float]] = None  # [minx, miny, maxx, maxy]
    confidence: float = 1.0
    is_valid: bool = True
    tolerance_pt: float = 5.0
