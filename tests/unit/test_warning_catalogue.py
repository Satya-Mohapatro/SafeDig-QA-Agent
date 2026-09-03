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
