"""
Retrieval Pydantic Schemas — Phase 3
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RetrievalFilter(BaseModel):
    crop: Optional[str] = Field(None, description="Filter by crop name (e.g. Wheat, Rice, Mustard)")
    topic: Optional[str] = Field(None, description="Filter by topic (e.g. Disease Management, Fertilizer, Irrigation)")
    institution: Optional[str] = Field(None, description="Filter by source institution (e.g. ICAR, PAU)")
    document_id: Optional[str] = Field(None, description="Filter by specific document ID")


class RetrievalRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Agricultural query in English or Hindi/Hinglish")
    filters: Optional[RetrievalFilter] = Field(None, description="Optional metadata filters")
    top_k: int = Field(5, ge=1, le=20, description="Number of final context chunks to return")
    enable_reranker: bool = Field(True, description="Whether to apply cross-encoder reranking")


class RetrievedChunkResponse(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    source_institution: str
    source_url: Optional[str] = None
    page_number: int
    section_heading: Optional[str] = None
    text: str
    crop_tags: List[str] = []
    topic_tags: List[str] = []
    language: str = "en"
    relevance_score: float
    retrieval_method: str
    dense_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    rrf_score: Optional[float] = None


class RetrievalResponse(BaseModel):
    question: str
    total_retrieved: int
    chunks: List[RetrievedChunkResponse]
    latency_ms: float
    filters_applied: Optional[Dict[str, Any]] = None


class IndexingStatusResponse(BaseModel):
    qdrant: Dict[str, Any]
    bm25: Dict[str, Any]
