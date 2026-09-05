import pytest
import httpx
from src.api.app import app
from src.batch import worker_pool
from tests.conftest import PROJECT_ROOT, DATA_DIR, SAMPLE_FOLDER_244414, SAMPLE_NGED_PDF

@pytest.mark.anyio
async def test_batch_api_endpoints_and_progress():
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # 1. Scan directory
            scan_resp = await client.post("/api/v1/batch/scan-directory", json={
                "parent_directory": str(DATA_DIR),
                "priority": 5
            })
            assert scan_resp.status_code == 200
            scan_data = scan_resp.json()
            assert scan_data["submitted_count"] == 13
            assert len(scan_data["job_ids"]) == 13
            
            # 2. Query Progress
            prog_resp = await client.get("/api/v1/batch/progress")
            assert prog_resp.status_code == 200
            prog_data = prog_resp.json()
            assert prog_data["total_jobs"] >= 13
            assert prog_data["max_workers"] >= 2
    finally:
        worker_pool.stop(timeout_sec=1.0)
