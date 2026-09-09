import pytest
from shapely.geometry import LineString, box
from src.spatial import spatial_engine, coordinate_transformer
from src.domain.aoi import AOI
from src.domain.enums import AOIDetectionMethod

def test_spatial_intersection():
    # AOI box from (100, 100) to (200, 200)
    aoi = AOI(
        aoi_id="AOI-1",
        document_id="DOC-1",
        page_num=1,
        method=AOIDetectionMethod.NATIVE_VECTOR,
        coordinates=list(box(100, 100, 200, 200).exterior.coords),
        bbox=[100, 100, 200, 200],
        is_valid=True
    )
    
    # Intersecting line: crosses from (50, 150) to (250, 150)
    line1 = LineString([(50, 150), (250, 150)])
    is_int1, dist1 = spatial_engine.check_intersection(line1, aoi)
    assert is_int1 is True
    assert dist1 == 0.0
    
    # Non-intersecting line: far outside at (500, 500) to (600, 600)
    line2 = LineString([(500, 500), (600, 600)])
    is_int2, dist2 = spatial_engine.check_intersection(line2, aoi)
    assert is_int2 is False
    assert dist2 > 200.0

def test_coordinate_transforms():
    px, py = coordinate_transformer.pdf_to_pixel(72.0, 144.0, dpi=300)
    assert px == 300
    assert py == 600
    
    pdf_x, pdf_y = coordinate_transformer.pixel_to_pdf(300, 600, dpi=300)
    assert pdf_x == 72.0
    assert pdf_y == 144.0
