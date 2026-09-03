from typing import Any, Tuple, Optional
from shapely.geometry import shape, Polygon, LineString, Point, box
from shapely import intersects, within, contains, distance
from src.domain.aoi import AOI

class SpatialEngine:
    @staticmethod
    def aoi_to_shapely(aoi: AOI) -> Optional[Polygon]:
        if not aoi.is_valid or not aoi.coordinates:
            if aoi.bbox:
                return box(*aoi.bbox)
            return None
        return Polygon(aoi.coordinates)

    @staticmethod
    def check_intersection(geometry: Any, aoi: AOI, tolerance_pt: float = 5.0) -> Tuple[bool, float]:
        aoi_poly = SpatialEngine.aoi_to_shapely(aoi)
        if aoi_poly is None or geometry is None:
            return False, 9999.0
            
        # If tolerance > 0, buffer AOI slightly
        test_aoi = aoi_poly.buffer(tolerance_pt) if tolerance_pt > 0 else aoi_poly
        
        is_intersecting = bool(test_aoi.intersects(geometry))
        dist = float(aoi_poly.distance(geometry))
        
        return is_intersecting, dist

spatial_engine = SpatialEngine()
