import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoints_and_legacy_demo_routes_are_not_exposed() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        health = await client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        live = await client.get("/api/health/live")
        assert live.status_code == 200

        legacy = await client.post("/api/practice/dictation", json={})
        assert legacy.status_code == 404


@pytest.mark.asyncio
async def test_ready_returns_service_unavailable_without_database() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ready = await client.get("/api/health/ready")
        assert ready.status_code == 503
