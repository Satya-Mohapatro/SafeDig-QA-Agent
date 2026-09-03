import pytest
import httpx
from src.api.app import app

@pytest.mark.anyio
async def test_eval_api_endpoints():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Trigger benchmark run
        run_resp = await client.post("/api/v1/eval/run")
        assert run_resp.status_code == 200
        run_data = run_resp.json()
        assert "run_id" in run_data
        assert run_data["safety_compliance_passed"] is True
        assert run_data["metrics"]["escaped_hazard_count"] == 0

        # 2. Fetch latest report
        resp = await client.get("/api/v1/eval/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"] == run_data["run_id"]
        assert data["safety_compliance_passed"] is True
        assert data["metrics"]["escaped_hazard_count"] == 0

