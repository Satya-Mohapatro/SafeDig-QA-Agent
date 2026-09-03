import pytest
import httpx
from src.api.app import app

@pytest.mark.anyio
async def test_health_check_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "HEALTHY"
        assert "AI Map QA" in data["app_name"]
        assert "engine_version" in data

@pytest.mark.anyio
async def test_job_submit_nonexistent_folder():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/jobs/submit", json={"root_dir": "d:/NonExistentPath_XYZ"})
        assert resp.status_code == 404
        assert "Target root folder not found" in resp.json()["detail"]

@pytest.mark.anyio
async def test_job_status_not_found():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/jobs/JOB-DOES-NOT-EXIST")
        assert resp.status_code == 404
