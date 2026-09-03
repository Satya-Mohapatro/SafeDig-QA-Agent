import pytest
from src.legends import master_legend_registry, resolve_legend

def test_legend_profiles():
    sgn_lgd = master_legend_registry.get_profile("SGN")
    assert sgn_lgd is not None
    assert sgn_lgd.version == "1.2.0"
    assert len(sgn_lgd.features) >= 2
    
    ukpn_lgd = resolve_legend("UKPN")
    assert ukpn_lgd is not None
    assert "UK Power" in ukpn_lgd.provider or ukpn_lgd.provider == "UKPN"

def test_missing_legend():
    unknown = resolve_legend("Unknown_Utility_X_999")
    assert unknown is None
