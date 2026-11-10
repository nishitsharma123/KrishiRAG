"""
Chat and RAG Pydantic Schemas — Phase 4
Strict validation for chat requests, grounded source citations, and RAG responses.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.retrieval import RetrievedChunkResponse


class SourceCitation(BaseModel):
    document_id: str
    document_title: str
    source_institution: str
    page_number: int
    section_heading: Optional[str] = None
    supporting_passage: str
    relevance_score: float
    is_verified: bool = True


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Persistent conversation session ID")
    question: str = Field(..., min_length=2, description="Farmer or user agricultural query")
    crop: Optional[str] = Field(None, description="Optional target crop filter")
    topic: Optional[str] = Field(None, description="Optional agronomic topic filter")


class ChatResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    sources: List[SourceCitation]
    retrieved_chunks: List[RetrievedChunkResponse]
    retrieval_time_ms: float
    generation_time_ms: float
    abstained: bool
    abstention_reason: Optional[str] = None


class MessageHistoryItem(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ConversationHistoryResponse(BaseModel):
    session_id: str
    conversation_id: str
    messages: List[MessageHistoryItem]
