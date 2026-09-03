from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Dict, Any
from .enums import GeometryType

class ColorSignature(BaseModel):
    rgb: Tuple[int, int, int]
    hsv_range: Optional[Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = None
    tolerance: int = 20

class StrokeStyle(BaseModel):
    min_width_pt: float = 0.5
    max_width_pt: float = 10.0
    dash_pattern: List[float] = Field(default_factory=list)

class LegendFeature(BaseModel):
    feature_id: str
    warning_code: str
    description: str
    geometry_type: GeometryType = GeometryType.LINE
    color: ColorSignature
    stroke: StrokeStyle
    text_labels: List[str] = Field(default_factory=list)

class LegendProfile(BaseModel):
    legend_id: str
    provider: str
    utility_type: str
    version: str = "1.0.0"
    effective_date: str = "2026-01-01"
    source_document: Optional[str] = None
    features: List[LegendFeature] = Field(default_factory=list)
