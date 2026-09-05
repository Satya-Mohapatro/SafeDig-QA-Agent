import os
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "Data"
SAMPLE_FOLDER_244414 = DATA_DIR / "244414_201678"
SAMPLE_NGED_PDF = SAMPLE_FOLDER_244414 / "42332089_NGED - Wales.pdf"

@pytest.fixture(scope="session")
def project_root_path() -> Path:
    return PROJECT_ROOT

@pytest.fixture(scope="session")
def data_dir_path() -> Path:
    return DATA_DIR

@pytest.fixture(scope="session")
def sample_folder_path() -> str:
    return str(SAMPLE_FOLDER_244414)
