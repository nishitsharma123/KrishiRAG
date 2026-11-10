"""
RAG Pipeline & Qwen3 Integration Tests — Phase 4
Tests grounding, evidence sufficiency abstention, citation validation,
conversation history, and live API endpoints.
"""

import os
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.database.session import SessionLocal, init_db
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.services.rag_service import rag_service
from backend.app.services.llm_service import llm_service


@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    init_db()


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


def test_ollama_service_availability():
    """Verify Ollama connection and qwen3:4b model installation."""
    status = llm_service.is_available()
    assert status["available"] is True, f"Ollama is unreachable: {status.get('error')}"
    assert status["model_installed"] is True, f"qwen3:4b not found in: {status.get('installed_models')}"


@pytest.mark.anyio
async def test_evidence_sufficiency_abstains_on_irrelevant_query():
    """Verify KrishiRAG explicitly abstains on non-agricultural queries."""
    irrelevant_q = "How do I change the brake pads on a Honda Civic?"
    response = await rag_service.answer_question(question=irrelevant_q)

    assert response.abstained is True
    assert response.abstention_reason is not None
    assert "insufficient" in response.answer.lower() or "not contain" in response.answer.lower()
    assert len(response.sources) == 0


@pytest.mark.anyio
async def test_evidence_sufficiency_abstains_on_unsupported_query():
    """Verify KrishiRAG explicitly abstains on unsupported agricultural crops."""
    unsupported_q = "How to cultivate dragon fruit in Antarctica sub-zero soil?"
    response = await rag_service.answer_question(question=unsupported_q)

    assert response.abstained is True
    assert "insufficient" in response.answer.lower() or "notice" in response.answer.lower()


@pytest.mark.anyio
async def test_rag_answers_wheat_seed_rate_with_citations():
    """Verify live Qwen3 RAG answer on authentic ICAR wheat cultivation question."""
    db = SessionLocal()
    try:
        query = "What is the recommended seed rate for timely sown wheat in NWPZ?"
        response = await rag_service.answer_question(
            question=query,
            session_id="test-wheat-session",
            db=db,
        )

        assert response.abstained is False
        assert len(response.answer) > 50
        assert response.retrieval_time_ms > 0
        assert response.generation_time_ms > 0
        assert len(response.sources) > 0

        # Validate that top source is an authentic ICAR publication with page number
        top_src = response.sources[0]
        assert top_src.document_title != ""
        assert top_src.page_number >= 1
        assert top_src.is_verified is True
        assert len(top_src.supporting_passage) > 20
    finally:
        db.close()


@pytest.mark.anyio
async def test_conversation_history_persistence():
    """Verify multi-turn conversation messages are persisted and retrieved.

    Uses a unique UUID session_id per test run to ensure complete isolation
    from previous test executions — prevents false assertion failures caused
    by stale messages from earlier runs sharing the same session_id.
    """
    db = SessionLocal()
    # Unique session per run — eliminates cross-run message count pollution
    session_id = f"test-multi-turn-{uuid.uuid4().hex}"
    try:
        # Turn 1
        r1 = await rag_service.answer_question(
            question="What are the critical irrigation stages for wheat?",
            session_id=session_id,
            db=db,
        )
        assert r1.abstained is False, f"Turn 1 abstained unexpectedly: {r1.abstention_reason}"

        # Turn 2 - Follow-up using same session
        r2 = await rag_service.answer_question(
            question="Which of these is the most critical stage if only one irrigation is available?",
            session_id=session_id,
            db=db,
        )
        assert r2.abstained is False, f"Turn 2 abstained unexpectedly: {r2.abstention_reason}"

        # Verify exactly 4 messages persisted for this fresh session
        conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
        assert conv is not None, "Conversation record was not created"
        msgs = db.query(Message).filter(Message.conversation_id == conv.id).all()
        assert len(msgs) == 4, (
            f"Expected 4 messages (2 user + 2 assistant), got {len(msgs)}. "
            f"Roles: {[m.role for m in msgs]}"
        )
        # Verify correct role ordering
        roles = [m.role for m in msgs]
        assert roles == ["user", "assistant", "user", "assistant"]
    finally:
        db.close()


@pytest.mark.anyio
async def test_api_chat_endpoint_contract():
    """Verify POST /api/chat adheres strictly to the Pydantic contract."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "session_id": "api-test-session",
            "question": "What is the recommended NPK dose for irrigated wheat?",
        }
        res = await ac.post("/api/chat", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert "answer" in data
        assert "sources" in data
        assert "retrieved_chunks" in data
        assert "retrieval_time_ms" in data
        assert "generation_time_ms" in data
        assert "abstained" in data
        assert data["abstained"] is False
        assert len(data["sources"]) > 0
