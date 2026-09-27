import os
import pytest
from src.pdf import inspect_pdf
from src.aoi import get_document_aoi
from src.legends.detector import detect_dynamic_legend
from src.legends.resolver import resolve_legend
from src.warnings import master_warning_catalogue
from src.detection.discovery import discover_open_world_assets

def test_dynamic_legend_detection_thames_water():
    pdf_path = "Data/539507_169488/Clean_Water.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip("Test PDF not found")
        
    profile = detect_dynamic_legend(pdf_path, "Thames Water", 1)
    assert profile is not None
    assert len(profile.features) >= 5
    feature_ids = [f.feature_id for f in profile.features]
    assert "TRUNK_MAIN" in feature_ids or "WATER_MAIN" in feature_ids
    assert profile.dynamic_confidence >= 0.80

def test_dynamic_legend_detection_sgn():
    pdf_path = "Data/539507_169488/42361245_SGN.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip("Test PDF not found")
        
    profile = detect_dynamic_legend(pdf_path, "SGN", 1)
    assert profile is not None
    assert len(profile.features) >= 4
    feature_ids = [f.feature_id for f in profile.features]
    assert any("PRESSURE" in fid or "GAS" in fid for fid in feature_ids)

def test_open_world_asset_discovery_and_classification_confidence():
    pdf_path = "Data/539507_169488/42361245_SGN.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip("Test PDF not found")
        
    doc = inspect_pdf(pdf_path, "DOC-TEST-SGN", "JOB-TEST", "1", "hash")
    aoi = get_document_aoi(pdf_path, "DOC-TEST-SGN", 1)
    legend = resolve_legend("SGN", pdf_path=pdf_path)
    wdefs = master_warning_catalogue.get_definitions_for_provider("SGN")
    
    assets, completeness = discover_open_world_assets(pdf_path, doc, aoi, legend, wdefs)
    assert len(assets) > 0
    assert completeness.overall >= 0.80
    
    # Check that canonical assets have classification confidence
    for a in assets:
        assert 0.0 <= a.classification_confidence <= 1.0
        assert 0.0 <= a.geometry_confidence <= 1.0
        assert a.spatial_relation in ["intersects", "crosses", "inside", "near", "outside"]
        assert a.segment_count >= 1

    # Verify ground truth asset detection: Low Pressure Gas Main (red 63 PE pipe) inside AOI
    lp_assets = [a for a in assets if "low pressure" in a.normalized_class.lower()]
    assert len(lp_assets) == 1
    assert lp_assets[0].inside_aoi is True
    assert lp_assets[0].classification_confidence >= 0.70

    # Verify no false positive High Pressure Gas Main inside the AOI
    hp_in_aoi = [a for a in assets if "high pressure" in a.normalized_class.lower() and a.inside_aoi]
    assert len(hp_in_aoi) == 0


def test_nget_letter_no_false_assets():
    """Verify National Grid Electricity letters/notices produce 0 false assets."""
    pdf_path = "Data/535179_175614/National Grid Electricity_42463390.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip("Test PDF not found")

    doc = inspect_pdf(pdf_path, "DOC-TEST-NGET", "JOB-TEST", "1", "hash")
    # Verify map page correctly auto-detected as page 3
    assert doc.map_page_num == 3
    assert doc.is_missing_map_data is True  # "No Assets Affected" notice

    aoi = get_document_aoi(pdf_path, "DOC-TEST-NGET", doc.map_page_num)
    assert aoi.page_num == 3
    assert "vector" in str(aoi.source).lower()

    legend = resolve_legend("National Grid Electricity Transmission", pdf_path=pdf_path, page_num=doc.map_page_num)
    wdefs = master_warning_catalogue.get_definitions_for_provider("National Grid Electricity Transmission")

    assets, completeness = discover_open_world_assets(pdf_path, doc, aoi, legend, wdefs)
    # Zero false assets (no 11kV cables or unknown assets from letterhead)
    assert len(assets) == 0
