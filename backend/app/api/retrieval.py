"""
Retrieval & Indexing API Router — Phase 3
Endpoints for triggering document indexing, inspecting index status,
and testing hybrid retrieval with real agricultural queries.
"""

import time
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.retrieval import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievedChunkResponse,
    IndexingStatusResponse,
)
from backend.app.services.retrieval_service import retrieve_context
from backend.app.services.indexing_pipeline import IndexingPipeline
from backend.app.services.vector_store import vector_store
from backend.app.services.bm25_service import bm25_service

router = APIRouter(prefix="/retrieval", tags=["Retrieval & Indexing"])


@router.post("/search", response_model=RetrievalResponse)
def search_knowledge_base(request: RetrievalRequest):
    """
    Execute hybrid retrieval (Dense + BM25 + RRF + Cross-Encoder Reranking)
    over indexed ICAR publications and return verified passage citations.
    """
    start_time = time.time()

    filters_dict = None
    if request.filters:
        filters_dict = {
            k: v for k, v in request.filters.model_dump().items() if v is not None
        }

    try:
        chunks = retrieve_context(
            question=request.question,
            filters=filters_dict,
            top_k=request.top_k,
            enable_reranker=request.enable_reranker,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval error: {str(e)}",
        )

    latency_ms = round((time.time() - start_time) * 1000, 2)

    return RetrievalResponse(
        question=request.question,
        total_retrieved=len(chunks),
        chunks=[RetrievedChunkResponse(**c.model_dump()) for c in chunks],
        latency_ms=latency_ms,
        filters_applied=filters_dict,
    )


@router.post("/index")
def trigger_indexing(force_rebuild: bool = False):
    """
    Trigger full batch embedding generation and indexing over all
    processed document JSON files in data/processed/.
    """
    try:
        result = IndexingPipeline.index_all_documents(force_rebuild=force_rebuild)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}",
        )


@router.get("/index/status", response_model=IndexingStatusResponse)
def get_indexing_status():
    """
    Return vector store collection statistics and BM25 index status.
    """
    qdrant_stats = vector_store.get_collection_stats()
    bm25_stats = bm25_service.get_stats()
    return IndexingStatusResponse(qdrant=qdrant_stats, bm25=bm25_stats)
