import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.core.config import settings
from app.db import init_db


# Ensure DB schema exists for tests (httpx ASGI client may not trigger startup events)
@pytest.fixture(scope="session", autouse=True)
def _ensure_db():
    init_db()

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/healthz")
        assert r.status_code == 200
        assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_ready():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/readyz")
        assert r.status_code == 200
        assert r.json()["ready"] is True


@pytest.mark.asyncio
async def test_metrics():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/metrics")
        assert r.status_code == 200
        # Basic sanity checks on Prometheus exposition format
        assert "# HELP" in r.text
        assert "text/plain" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_query_ping():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get(f"{settings.API_PREFIX}/query/ping")
        assert r.status_code == 200
        assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_query_documents_get_requires_question():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Missing required 'question' should 422
        r = await ac.get(f"{settings.API_PREFIX}/query/documents")
        assert r.status_code == 422


@pytest.mark.asyncio
async def test_query_documents_post_requires_body():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Missing JSON body should 422
        r = await ac.post(f"{settings.API_PREFIX}/query/documents")
        assert r.status_code == 422


@pytest.mark.asyncio
async def test_upload_no_files():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # No files provided -> 400
        r = await ac.post(f"{settings.API_PREFIX}/upload", files={})
        assert r.status_code == 422
        assert r.json()["detail"] == [{'input': None, 'loc': ['body', 'files'], 'msg': 'Field required', 'type': 'missing'}]


@pytest.mark.asyncio
async def test_upload_then_query_documents():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1) Upload a simple text file mentioning Delaware law
        content = b"This Non-Disclosure Agreement is governed by Delaware law."
        files = [("files", ("sample_delaware_nda.txt", content, "text/plain"))]
        ur = await ac.post(f"{settings.API_PREFIX}/upload", files=files)
        assert ur.status_code == 200
        body = ur.json()
        assert body.get("status") == "accepted"
        assert body.get("count") == 1

        # 2) Poll the query endpoint until the background task ingests the doc
        found = False
        for _ in range(20):  # up to ~2s
            qr = await ac.post(
                f"{settings.API_PREFIX}/query/documents",
                json={"question": "Find documents governed by Delaware law"},
            )
            assert qr.status_code == 200
            hits = qr.json()
            if any(h.get("document") == "sample_delaware_nda.txt" for h in hits):
                found = True
                break
            await asyncio.sleep(0.1)

        assert found, "Uploaded document should be retrievable via governing law filter"
