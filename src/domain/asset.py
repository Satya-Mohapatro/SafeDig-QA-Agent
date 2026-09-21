from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from src.domain.enums import GeometryType, Severity

class DiscoveredAsset(BaseModel):
    asset_id: str
    document_id: str
    page_num: int = 1
    normalized_class: str
    raw_legend_label: Optional[str] = None
    utility: str = "Unknown"
    utility_type: str = "Unknown"
    
    # Visual & geometric properties
    geometry_type: GeometryType = GeometryType.LINE
    color_hex: str = "#FF0000"
    color_rgb: List[int] = Field(default_factory=lambda: [255, 0, 0])
    stroke_style: str = "solid"  # solid, dashed, dotted
    stroke_width_pt: float = 1.5
    coordinates: List[Any] = Field(default_factory=list)
    bbox: List[float] = Field(default_factory=list)
    segment_count: int = 1
    
    # Spatial relationship with AOI
    inside_aoi: bool = False
    spatial_relation: str = "outside"  # intersects, crosses, inside, near, outside
    aoi_distance_pt: float = 0.0
    
    # Confidences
    classification_confidence: float = 0.95  # Confidence that detected asset matches legend class
    geometry_confidence: float = 0.99        # Vector = 0.99, Raster = 0.85
    spatial_confidence: float = 0.99         # Deterministic Shapely intersection confidence
    visual_confidence: float = 0.95
    overall_confidence: float = 0.95
    
    # Contractual alignment
    contract_match: bool = False
    warning_code: Optional[str] = None
    business_warning_text: Optional[str] = None
    severity: Severity = Severity.UNKNOWN
    
    # Evidence & status
    status: str = "CONFIRMED"  # CONFIRMED, CORROBORATED, LIKELY, POSSIBLE, UNKNOWN, NEEDS_REVIEW
    evidence_crop_path: Optional[str] = None
    legend_crop_path: Optional[str] = None
    detection_methods: List[str] = Field(default_factory=lambda: ["pdf_vector"])
    notes: List[str] = Field(default_factory=list)

class ScanCompleteness(BaseModel):
    aoi_coverage: float = 1.0
    legend_confidence: float = 0.95
    image_quality: float = 0.98
    analysis_coverage: float = 1.0
    unknown_object_count: int = 0
    pages_analyzed: int = 1
    overall: float = 0.95
    status: str = "COMPLETE"  # COMPLETE, HIGH, INSUFFICIENT
