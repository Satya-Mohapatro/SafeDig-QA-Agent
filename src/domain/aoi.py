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
    # Structured evidence fields (added for AOI pipeline transparency)
    map_region: Optional[List[float]] = None       # [x0,y0,x1,y1] detected map-canvas bbox (excl. legend/footer)
    source: Optional[str] = None                   # e.g. "dashed_vector_boundary", "cv_contour", "map_region_fallback"
    evidence: List[str] = Field(default_factory=list)  # human-readable explanation of detection
    circle_center: Optional[List[float]] = None    # [cx, cy] if geometry_type == CIRCLE
    circle_radius: Optional[float] = None          # radius in PDF pts if geometry_type == CIRCLE
