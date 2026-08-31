import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_and_import_lifecycle() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        health = await client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        created = await client.post(
            "/api/immersion/imports",
            json={"source_url": "https://www.youtube.com/watch?v=lesson", "accent": "en-US"},
        )
        assert created.status_code == 202
        job_id = created.json()["id"]

        advanced = await client.post(f"/api/immersion/imports/{job_id}/advance")
        assert advanced.json()["status"] == "fetching"


@pytest.mark.asyncio
async def test_rejects_unapproved_video_source_and_scores_dictation() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        rejected = await client.post(
            "/api/immersion/imports",
            json={"source_url": "https://example.com/video", "accent": "en-US"},
        )
        assert rejected.status_code == 422

        result = await client.post(
            "/api/practice/dictation",
            json={
                "segment_id": "7f5b73e7-6c2a-4e78-b1aa-d11fc7eff2c4",
                "answer": "Learning takes practice",
                "reference": "Learning takes daily practice",
            },
        )
        assert result.status_code == 200
        assert result.json()["score"] == 75


@pytest.mark.asyncio
async def test_rejects_private_network_import_url() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        rejected = await client.post(
            "/api/immersion/imports",
            json={"source_url": "https://127.0.0.1/video", "accent": "en-US"},
        )
        assert rejected.status_code == 422
