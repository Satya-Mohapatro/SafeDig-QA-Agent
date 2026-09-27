import pytest
from src.warnings import master_warning_catalogue
from src.domain.enums import Severity

def test_master_catalogue_loaded():
    assert len(master_warning_catalogue.definitions) > 0
    
    # Check SGN definitions
    sgn_defs = master_warning_catalogue.get_definitions_for_provider("SGN")
    assert len(sgn_defs) >= 1
    
    # Check find by text
    wdef = master_warning_catalogue.find_by_text("There is a High Pressure Gas Line in this area")
    assert wdef is not None
    assert wdef.severity == Severity.HIGH
    assert wdef.provider == "SGN"


def test_catalogue_api_endpoint():
    from fastapi.testclient import TestClient
    from src.api.app import create_app

    app = create_app()
    client = TestClient(app)

    # Test full catalogue
    resp = client.get("/api/v1/catalogue")
    assert resp.status_code == 200
    data = resp.json()
    assert "stats" in data
    assert "providers" in data
    assert data["stats"]["total_providers"] >= 40
    assert data["stats"]["high_hazard_warnings"] >= 20

    # Test domain filtering
    resp_gas = client.get("/api/v1/catalogue?utility_type=Gas")
    assert resp_gas.status_code == 200
    gas_data = resp_gas.json()
    assert all(p["utility_type"] == "Gas" for p in gas_data["providers"])

    # Test provider lookup
    resp_sgn = client.get("/api/v1/catalogue/provider/SGN")
    assert resp_sgn.status_code == 200
    sgn = resp_sgn.json()
    assert sgn["utility_name"] == "SGN"
    assert "legend" in sgn
    assert len(sgn["legend"]["features"]) >= 4
