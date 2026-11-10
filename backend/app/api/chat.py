"""
Chat API Router — Phase 4 & Phase 5
Exposes endpoints for grounded RAG question answering, conversation history,
session management, feedback collection, and Ollama LLM status inspection.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database.session import get_db
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.models.feedback import Feedback
from backend.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    MessageHistoryItem,
)
from backend.app.services.rag_service import rag_service
from backend.app.services.llm_service import llm_service

router = APIRouter(prefix="/chat", tags=["RAG Chatbot"])


class FeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(..., ge=-1, le=5, description="1 for helpful, -1 for unhelpful")
    comment: Optional[str] = None


class SessionSummary(BaseModel):
    session_id: str
    message_count: int
    preview: str
    created_at: str


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


@router.get("/sessions", response_model=List[SessionSummary])
def list_sessions(db: Session = Depends(get_db)):
    """
    List all previous conversation sessions with their first message preview and count.
    """
    conversations = (
        db.query(Conversation)
        .order_by(desc(Conversation.created_at))
        .all()
    )

    results = []
    for conv in conversations:
        msgs = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        if not msgs:
            continue
        first_user_q = next((m.content for m in msgs if m.role == "user"), "New advisory session")
        preview = first_user_q[:60] + ("..." if len(first_user_q) > 60 else "")
        results.append(
            SessionSummary(
                session_id=conv.session_id,
                message_count=len(msgs),
                preview=preview,
                created_at=conv.created_at.isoformat() if conv.created_at else "",
            )
        )
    return results


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """
    Delete a conversation session and all its messages.
    """
    conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation session not found")

    db.delete(conv)
    db.commit()
    return {"success": True, "message": f"Session '{session_id}' deleted successfully."}


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


@router.post("/feedback")
def submit_feedback(fb_req: FeedbackRequest, db: Session = Depends(get_db)):
    """
    Submit helpful / not helpful feedback for an assistant response.
    """
    existing = db.query(Feedback).filter(Feedback.message_id == fb_req.message_id).first()
    if existing:
        existing.rating = fb_req.rating
        existing.comment = fb_req.comment
        db.commit()
        return {"success": True, "message": "Feedback updated"}

    new_fb = Feedback(
        message_id=fb_req.message_id,
        rating=fb_req.rating,
        comment=fb_req.comment,
    )
    db.add(new_fb)
    db.commit()
    return {"success": True, "message": "Feedback registered"}


@router.get("/status")
def get_llm_status():
    """
    Check Ollama connection health and model availability.
    """
    return llm_service.is_available()
