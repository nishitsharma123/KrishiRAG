import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.database.session import init_db, SessionLocal
from backend.app.models.document import Document

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

def test_database_initialization():
    init_db()
    db = SessionLocal()
    try:
        count = db.query(Document).count()
        assert count >= 0
    finally:
        db.close()

@pytest.mark.anyio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "KrishiRAG"
    assert data["database_connected"] is True
    assert "system_metrics" in data
    assert "vector_db_path" in data

@pytest.mark.anyio
async def test_root_redirect():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/", follow_redirects=False)
    assert response.status_code in [302, 307]
    assert response.headers["location"] == "/docs"

@pytest.mark.anyio
async def test_documents_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
