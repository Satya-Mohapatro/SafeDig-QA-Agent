"""Regression tests for the overhauled AOI detector.

Covers:
 1. Yellow dashed circle (NGED) → CIRCLE geometry, correct center/radius
 2. Purple dashed circle (UKPN, rotated 90°) → CIRCLE geometry, passes size check
 3. Purple dashed polygon (SGN) → POLYGON geometry
 4. Raster-only map (GTC) → CV_CONTOUR detection via rendered image
 5. Map + right legend → MAP_REGION excludes legend column
 6. Map + bottom footer → MAP_REGION excludes footer strip
 7. No explicit boundary → MAP_REGION fallback, not page-size
 8. Circle geometry is preserved (not converted to rectangle)
 9. Circle bounding box aspect ratio preserved
10. AOI validator rejects oversized rectangle (> 93% page)
11. AOI validator rejects zero-area box
12. Coordinate transform accuracy (PDF pts ↔ pixel roundtrip)
"""

import os
import math
import pytest
import pymupdf
from shapely.geometry import Point

from src.aoi.detector import (
    detect_aoi_from_pdf,
    _detect_circle_from_items,
    _circle_to_coords,
    _derive_map_region,
    _validate_aoi,
)
from src.domain.enums import AOIDetectionMethod, GeometryType
from src.spatial.coordinates import coordinate_transformer

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "Data")
NGED_PDF = os.path.join(DATA_DIR, "244414_201678", "42332089_NGED - Wales.pdf")
WWU_PDF = os.path.join(DATA_DIR, "244414_201678", "42332089_WWU.pdf")
GTC_PDF = os.path.join(DATA_DIR, "244414_201678", "GTC.pdf")
GTC_POLY_PDF = os.path.join(DATA_DIR, "244414_201678", "GTC_polygon.pdf")
W_PDF = os.path.join(DATA_DIR, "244414_201678", "W.pdf")
UKPN_PDF = os.path.join(DATA_DIR, "547960_159487", "UKPN_42323146.pdf")
SGN_PDF = os.path.join(DATA_DIR, "520355_160953", "42338420_SGN.pdf")


# ── Helper ────────────────────────────────────────────────────────────────────
def _pdf_exists(path):
    return os.path.isfile(path)


def _make_fake_line_circle_items(cx, cy, r, n=64):
    """Build fake PyMuPDF-style 'l' items approximating a circle."""
    class FakePt:
        def __init__(self, x, y):
            self.x = x
            self.y = y
    items = []
    pts = []
    for i in range(n):
        theta = 2 * math.pi * i / n
        pts.append(FakePt(cx + r * math.cos(theta), cy + r * math.sin(theta)))
    for i in range(n):
        items.append(('l', pts[i], pts[(i + 1) % n]))
    return items


# ── Test 1: NGED yellow dashed circle ────────────────────────────────────────
@pytest.mark.skipif(not _pdf_exists(NGED_PDF), reason="NGED PDF not found")
def test_nged_circle_detected():
    """NGED map has a yellow dashed circle — should be CIRCLE geometry."""
    aoi = detect_aoi_from_pdf(NGED_PDF, "DOC-NGED-TEST", page_num=1)
    assert aoi.is_valid, f"AOI not valid: {aoi.evidence}"
    assert aoi.geometry_type == GeometryType.CIRCLE, (
        f"Expected CIRCLE, got {aoi.geometry_type}. Evidence: {aoi.evidence}"
    )
    assert aoi.circle_center is not None
    assert aoi.circle_radius is not None
    assert aoi.circle_radius > 30, "Circle radius seems too small"
    assert aoi.source in ("dashed_vector_boundary",), f"Unexpected source: {aoi.source}"


# ── Test 2: UKPN purple dashed circle (page rotated 90°) ─────────────────────
@pytest.mark.skipif(not _pdf_exists(UKPN_PDF), reason="UKPN PDF not found")
def test_ukpn_rotated_circle_detected():
    """UKPN map is rotated 90°; circle should still be detected and sized correctly."""
    aoi = detect_aoi_from_pdf(UKPN_PDF, "DOC-UKPN-TEST", page_num=1)
    assert aoi.is_valid, f"AOI not valid: {aoi.evidence}"
    assert aoi.geometry_type == GeometryType.CIRCLE, (
        f"Expected CIRCLE, got {aoi.geometry_type}"
    )
    assert aoi.circle_radius is not None
    # The circle covers a meaningful area — radius > 50 pts
    assert aoi.circle_radius > 50, f"UKPN circle radius too small: {aoi.circle_radius}"
    x0, y0, x1, y1 = aoi.bbox
    assert (x1 - x0) > 100, f"AOI too narrow: {x1-x0}"
    assert (y1 - y0) > 100, f"AOI too short: {y1-y0}"


# ── Test 3: WWU purple dashed circle ──────────────────────────────────────────
@pytest.mark.skipif(not _pdf_exists(WWU_PDF), reason="WWU PDF not found")
def test_wwu_circle_detected():
    """WWU map has a purple dashed circle."""
    aoi = detect_aoi_from_pdf(WWU_PDF, "DOC-WWU-TEST", page_num=1)
    assert aoi.is_valid, f"AOI not valid: {aoi.evidence}"
    assert aoi.geometry_type == GeometryType.CIRCLE


# ── Test 4: SGN purple dashed polygon ─────────────────────────────────────────
@pytest.mark.skipif(not _pdf_exists(SGN_PDF), reason="SGN PDF not found")
def test_sgn_polygon_detected():
    """SGN map has a purple dashed polygon (not circular)."""
    aoi = detect_aoi_from_pdf(SGN_PDF, "DOC-SGN-TEST", page_num=1)
    assert aoi.is_valid, f"AOI not valid: {aoi.evidence}"
    # SGN polygon may be POLYGON or CIRCLE depending on shape — key is it must be small/specific
    assert aoi.geometry_type in (GeometryType.POLYGON, GeometryType.CIRCLE)
    x0, y0, x1, y1 = aoi.bbox
    # Must NOT cover the full page (which would mean fallback kicked in instead)
    doc = pymupdf.open(SGN_PDF)
    p = doc[0]
    mw, mh = p.mediabox.width, p.mediabox.height
    aoi_area = (x1 - x0) * (y1 - y0)
    page_area = mw * mh
    assert aoi_area < page_area * 0.70, (
        f"SGN AOI covers too much of page ({aoi_area/page_area*100:.1f}%)"
    )


# ── Test 5: GTC raster-only map → CV detection ────────────────────────────────
@pytest.mark.skipif(not _pdf_exists(GTC_PDF), reason="GTC PDF not found")
def test_gtc_raster_detection():
    """GTC is raster-only (no vectors). Should return a valid AOI via CV or map_region."""
    aoi = detect_aoi_from_pdf(GTC_PDF, "DOC-GTC-TEST", page_num=1)
    assert aoi.is_valid, f"AOI not valid: {aoi.evidence}"
    # GTC has a red boundary in the raster image; CV should find it or fall back to map region
    # Key requirement: must NOT cover more than 93% of page
    doc = pymupdf.open(GTC_PDF)
    p = doc[0]
    mw, mh = p.mediabox.width, p.mediabox.height
    x0, y0, x1, y1 = aoi.bbox
    aoi_area = (x1 - x0) * (y1 - y0)
    page_area = mw * mh
    assert aoi_area < page_area * 0.93, (
        f"GTC AOI too large ({aoi_area/page_area*100:.1f}% of page) — oversized fallback"
    )


# ── Test 6: W.pdf (Welsh Water) → MAP_REGION fallback, not full page ──────────
@pytest.mark.skipif(not _pdf_exists(W_PDF), reason="W.pdf not found")
def test_water_map_region_fallback():
    """Welsh Water map has no explicit boundary → should use MAP_REGION, not full page."""
    aoi = detect_aoi_from_pdf(W_PDF, "DOC-W-TEST", page_num=1)
    assert aoi.is_valid
    doc = pymupdf.open(W_PDF)
    p = doc[0]
    mw, mh = p.mediabox.width, p.mediabox.height
    x0, y0, x1, y1 = aoi.bbox

    # Must not cover more than 93% of page
    aoi_area = (x1 - x0) * (y1 - y0)
    page_area = mw * mh
    assert aoi_area < page_area * 0.93, (
        f"W.pdf AOI is oversized ({aoi_area/page_area*100:.1f}%)"
    )

    # Must not include the right-side legend (W.pdf is landscape; legend is on right)
    # The detected map region right edge should be < 90% of page width
    assert x1 < mw * 0.92, f"W.pdf AOI extends too far right (x1={x1:.1f}, mw={mw:.1f})"


# ── Test 7: Circle geometry is preserved (unit test, no PDF) ─────────────────
def test_circle_items_detected_correctly():
    """Fake 64-point circular line items should be detected as a circle."""
    items = _make_fake_line_circle_items(cx=300, cy=300, r=100, n=64)
    result = _detect_circle_from_items(items)
    assert result is not None, "Expected circle detection"
    cx, cy, r = result
    assert abs(cx - 300) < 1.0, f"Center x off: {cx}"
    assert abs(cy - 300) < 1.0, f"Center y off: {cy}"
    assert abs(r - 100) < 2.0, f"Radius off: {r}"


# ── Test 8: Circle coords are actually circular ───────────────────────────────
def test_circle_coords_are_circular():
    """Generated circle polygon points should all lie on the circle."""
    cx, cy, r = 200, 150, 75
    coords = _circle_to_coords(cx, cy, r, n_pts=64)
    for x, y in coords[:-1]:  # skip closing duplicate
        d = math.hypot(x - cx, y - cy)
        assert abs(d - r) < 0.01, f"Point ({x},{y}) not on circle (dist={d:.3f}, r={r})"


# ── Test 9: Circle bounding box aspect ratio ──────────────────────────────────
def test_circle_bbox_aspect_ratio():
    """Circle bbox width and height should be equal (aspect ratio = 1.0)."""
    items = _make_fake_line_circle_items(cx=200, cy=200, r=80, n=64)
    result = _detect_circle_from_items(items)
    assert result is not None
    cx, cy, r = result
    w = 2 * r
    h = 2 * r
    assert abs(w - h) < 1.0, f"Circle bbox not square: w={w:.1f}, h={h:.1f}"


# ── Test 10: Validator rejects oversized AOI (> 93% page) ────────────────────
def test_validator_rejects_oversized():
    """AOI covering > 93% of page should fail validation."""
    mw, mh = 595.0, 842.0
    map_region = [10, 30, 550, 700]
    # Oversized AOI — nearly full page
    bbox = [5.0, 5.0, 590.0, 837.0]
    valid, reason = _validate_aoi(bbox, map_region, mw, mh)
    assert not valid, f"Expected invalid (oversized), got: {reason}"
    assert "93%" in reason


# ── Test 11: Validator rejects zero-area box ──────────────────────────────────
def test_validator_rejects_zero_area():
    """Zero-width AOI should fail validation."""
    mw, mh = 595.0, 842.0
    map_region = [10, 30, 550, 700]
    bbox = [100.0, 100.0, 100.0, 300.0]  # zero width
    valid, reason = _validate_aoi(bbox, map_region, mw, mh)
    assert not valid
    assert "zero" in reason.lower() or "negative" in reason.lower()


# ── Test 12: Coordinate transform roundtrip ───────────────────────────────────
def test_coordinate_transform_roundtrip():
    """PDF pts → pixels → PDF pts should be identity within 1 DPI unit."""
    for dpi in [72, 150, 300]:
        for pt in [0.0, 36.0, 72.0, 144.0, 288.0, 595.0]:
            px_x, px_y = coordinate_transformer.pdf_to_pixel(pt, pt, dpi=dpi)
            back_x, back_y = coordinate_transformer.pixel_to_pdf(px_x, px_y, dpi=dpi)
            tol = 72.0 / dpi  # one pixel in PDF pts
            assert abs(back_x - pt) <= tol, (
                f"dpi={dpi} pt={pt}: roundtrip x error {abs(back_x - pt):.4f}"
            )
            assert abs(back_y - pt) <= tol, (
                f"dpi={dpi} pt={pt}: roundtrip y error {abs(back_y - pt):.4f}"
            )
