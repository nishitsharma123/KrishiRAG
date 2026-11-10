"""
Chat API Router — Phase 4
Exposes endpoints for grounded RAG question answering, conversation history,
and Ollama LLM status inspection.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    MessageHistoryItem,
)
from backend.app.services.rag_service import rag_service
from backend.app.services.llm_service import llm_service

router = APIRouter(prefix="/chat", tags=["RAG Chatbot"])


@router.post("", response_model=ChatResponse)
async def ask_question(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Submit an agricultural question to the KrishiRAG pipeline.
    Executes:
    1. Hybrid Retrieval & Reranking
    2. Evidence Sufficiency Check (abstains if unsupported)
    3. Grounded Qwen3 4B Generation via Ollama
    4. Citation Validation against retrieved chunks
    5. Conversation persistence
    """
    try:
        response = await rag_service.answer_question(
            question=request.question,
            session_id=request.session_id,
            crop=request.crop,
            topic=request.topic,
            db=db,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat generation error: {str(e)}",
        )


@router.get("/history/{session_id}", response_model=ConversationHistoryResponse)
def get_conversation_history(session_id: str, db: Session = Depends(get_db)):
    """
    Retrieve message history for a given session ID.
    """
    conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation session not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return ConversationHistoryResponse(
        session_id=session_id,
        conversation_id=conv.id,
        messages=[
            MessageHistoryItem(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at.isoformat() if m.created_at else "",
            )
            for m in messages
        ],
    )


@router.get("/status")
def get_llm_status():
    """
    Check Ollama connection health and model availability.
    """
    return llm_service.is_available()
