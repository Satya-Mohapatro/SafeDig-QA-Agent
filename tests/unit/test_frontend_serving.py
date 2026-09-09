import pytest
import httpx
from src.api.app import app

@pytest.mark.anyio
async def test_frontend_index_serving():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "SafeDig" in resp.text
        assert "Map QA Workspace" in resp.text
        assert "Human Review Queue" in resp.text

@pytest.mark.anyio
async def test_frontend_static_css():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/static/styles.css")
        assert resp.status_code == 200
        assert "SafeDig QA Console" in resp.text
