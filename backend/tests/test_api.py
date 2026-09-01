import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoints_and_legacy_demo_routes_are_not_exposed() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        health = await client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        assert health.headers["x-request-id"]

        traced = await client.get("/api/v1/health", headers={"x-request-id": "test-request-42"})
        assert traced.headers["x-request-id"] == "test-request-42"

        live = await client.get("/api/v1/health/live")
        assert live.status_code == 200

        legacy = await client.post("/api/practice/dictation", json={})
        assert legacy.status_code == 404
        assert (await client.get("/api/health")).status_code == 404


@pytest.mark.asyncio
async def test_ready_returns_service_unavailable_without_database() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ready = await client.get("/api/v1/health/ready")
        assert ready.status_code == 503


@pytest.mark.asyncio
async def test_cors_allows_owner_refresh_cookie_for_allowed_origin() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-credentials"] == "true"
