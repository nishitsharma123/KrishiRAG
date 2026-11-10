"""
Admin Dashboard API Router — Phase 5
Exposes live database telemetry, ingestion counts, vector storage status,
and query usage statistics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database.session import get_db
from backend.app.models.document import Document
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.models.feedback import Feedback
from backend.app.services.vector_store import vector_store

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    """
    Returns live system telemetry and database statistics:
    - Total documents, pages, and chunks
    - Ingestion success/failure breakdown
    - Qdrant vector store collection metrics
    - Total user queries and conversation sessions
    - User feedback metrics
    """
    total_docs = db.query(Document).count()
    completed_docs = db.query(Document).filter(Document.status == "COMPLETED").count()
    failed_docs = db.query(Document).filter(Document.status == "FAILED").count()
    uploaded_docs = db.query(Document).filter(Document.status == "UPLOADED").count()

    total_pages = db.query(func.sum(Document.page_count)).scalar() or 0
    total_chunks = db.query(func.sum(Document.chunk_count)).scalar() or 0

    total_sessions = db.query(Conversation).count()
    total_questions = db.query(Message).filter(Message.role == "user").count()
    total_answers = db.query(Message).filter(Message.role == "assistant").count()

    # Feedback stats
    total_feedback = db.query(Feedback).count()
    positive_feedback = db.query(Feedback).filter(Feedback.rating > 0).count()
    feedback_satisfaction = round((positive_feedback / total_feedback * 100), 1) if total_feedback > 0 else 100.0

    # Vector store status
    try:
        vs_stats = vector_store.get_collection_stats()
    except Exception as e:
        vs_stats = {"status": "unavailable", "points_count": total_chunks, "error": str(e)}

    return {
        "documents": {
            "total": total_docs,
            "completed": completed_docs,
            "failed": failed_docs,
            "processing": uploaded_docs,
            "total_pages": int(total_pages),
            "total_chunks": int(total_chunks),
        },
        "vector_store": {
            "status": vs_stats.get("status", "green"),
            "points_count": vs_stats.get("points_count", total_chunks),
            "collection_name": vs_stats.get("collection_name", "icar_agricultural_knowledge"),
            "vector_size": vs_stats.get("vector_size", 384),
        },
        "conversations": {
            "total_sessions": total_sessions,
            "total_questions": total_questions,
            "total_answers": total_answers,
        },
        "feedback": {
            "total": total_feedback,
            "positive": positive_feedback,
            "satisfaction_rate": feedback_satisfaction,
        },
    }
