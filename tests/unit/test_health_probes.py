"""Unit tests for liveness and readiness health probes."""

import pytest
import httpx
from src.api.app import create_app

@pytest.mark.asyncio
async def test_liveness_probe():
    app = create_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "HEALTHY"
        assert "uptime_seconds" in data
        assert data["service"] == "safedig-map-qa-agent"

@pytest.mark.asyncio
async def test_readiness_probe():
    app = create_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "READY"
        assert "checks" in data
        assert "warning_catalogue" in data["checks"]
        assert "output_directory" in data["checks"]
        assert "database" in data["checks"]
        assert "READY" in data["checks"]["warning_catalogue"]
