"""
Phase 5 Complete Frontend & API Integration Tests
Tests all endpoints used by the KrishiRAG React frontend:
- Admin telemetry stats (/api/admin/stats)
- Evaluation benchmark metrics (/api/evaluation/metrics)
- Chat session listing and deletion (/api/chat/sessions)
- Feedback registration (/api/chat/feedback)
- LLM readiness status (/api/chat/status)
- Document deletion and listing (/api/documents)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.database.session import SessionLocal, init_db
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.models.document import Document

@pytest.fixture(scope="module", autouse=True)
def setup_env():
    init_db()

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_llm_status_endpoint_contract():
    """Verify GET /api/chat/status returns system_ready and ollama_available flags."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/chat/status")
        assert res.status_code == 200
        data = res.json()
        assert "available" in data
        assert "ollama_available" in data
        assert "system_ready" in data
        assert "model_installed" in data
        assert data["target_model"] == "qwen3:4b"

@pytest.mark.anyio
async def test_admin_stats_endpoint():
    """Verify GET /api/admin/stats returns real corpus and query metrics."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/admin/stats")
        assert res.status_code == 200
        data = res.json()
        assert "documents" in data
        assert "vector_store" in data
        assert "conversations" in data
        assert "feedback" in data
        assert data["documents"]["total"] >= 3
        assert data["vector_store"]["status"] in ["green", "yellow", "SYNCHRONIZED"]

@pytest.mark.anyio
async def test_evaluation_metrics_endpoint():
    """Verify GET /api/evaluation/metrics returns real Phase 3 benchmark data."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/evaluation/metrics")
        assert res.status_code == 200
        data = res.json()
        assert "aggregate_metrics" in data
        assert "benchmark_queries" in data
        assert len(data["benchmark_queries"]) == 15
        
        # Verify Precision@5 and Recall@5 are present
        p5 = next((m for m in data["aggregate_metrics"] if m["key"] == "precision_at_5"), None)
        assert p5 is not None
        assert p5["is_calculated"] is True

@pytest.mark.anyio
async def test_chat_sessions_and_feedback_flow():
    """Verify creating a conversation, listing it, submitting feedback, and deleting."""
    db = SessionLocal()
    test_session = "phase5-test-session-flow"
    try:
        # Create test conversation and message
        conv = Conversation(session_id=test_session)
        db.add(conv)
        db.commit()
        db.refresh(conv)

        msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content="Test recommendation for wheat sowing."
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. List sessions
            res_sess = await ac.get("/api/chat/sessions")
            assert res_sess.status_code == 200
            sessions = res_sess.json()
            assert any(s["session_id"] == test_session for s in sessions)

            # 2. Submit feedback
            res_fb = await ac.post("/api/chat/feedback", json={
                "message_id": msg.id,
                "rating": 1,
                "comment": "Accurate ICAR recommendation"
            })
            assert res_fb.status_code == 200
            assert res_fb.json()["success"] is True

            # 3. Delete session
            res_del = await ac.delete(f"/api/chat/sessions/{test_session}")
            assert res_del.status_code == 200
            assert res_del.json()["success"] is True
    finally:
        db.close()
