"""
Hybrid Retrieval and Cross-Encoder Reranking Service — Phase 3

Implements:
1. Dense Retrieval (multilingual-e5-small via Qdrant) -> Top 10
2. Sparse Retrieval (BM25Okapi) -> Top 10
3. Reciprocal Rank Fusion (RRF, k=60) to merge and deduplicate candidates
4. Cross-Encoder Reranking (ms-marco-MiniLM-L-6-v2) -> Top 4-5 final chunks
5. Memory management: strictly sequential evaluation, bounded batch inference.
"""

from __future__ import annotations

import gc
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.services.embedding_service import embedding_service
from backend.app.services.vector_store import vector_store
from backend.app.services.bm25_service import bm25_service

logger = logging.getLogger(__name__)


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    source_institution: str
    source_url: Optional[str] = None
    page_number: int
    section_heading: Optional[str] = None
    text: str
    crop_tags: List[str] = Field(default_factory=list)
    topic_tags: List[str] = Field(default_factory=list)
    language: str = "en"
    relevance_score: float
    retrieval_method: str  # "hybrid_reranked", "dense", "bm25"
    dense_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    rrf_score: Optional[float] = None


class RerankerService:
    """Singleton wrapper around cross-encoder/ms-marco-MiniLM-L-6-v2."""

    _instance: Optional["RerankerService"] = None
    _model = None

    def __new__(cls) -> "RerankerService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_model(self):
        if self._model is not None:
            return self._model

        from sentence_transformers import CrossEncoder

        logger.info("Loading cross-encoder reranker: %s", settings.RERANKER_MODEL_NAME)
        try:
            self._model = CrossEncoder(
                settings.RERANKER_MODEL_NAME,
                max_length=512,
                device="cpu",
                local_files_only=True,
            )
        except Exception:
            self._model = CrossEncoder(
                settings.RERANKER_MODEL_NAME,
                max_length=512,
                device="cpu",
            )
        return self._model

    def unload(self):
        if self._model is not None:
            logger.info("Unloading cross-encoder reranker to release RAM.")
            del self._model
            self._model = None
            gc.collect()

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Score (query, chunk_text) pairs and return top_k candidates sorted by cross-encoder score.
        """
        if not candidates:
            return []

        model = self._load_model()
        pairs = [[query, c.get("text", "")] for c in candidates]

        scores = model.predict(pairs, batch_size=8, show_progress_bar=False)

        # Attach reranker scores
        reranked = []
        for cand, score in zip(candidates, scores):
            item = dict(cand)
            item["relevance_score"] = float(score)
            item["retrieval_method"] = "hybrid_reranked"
            reranked.append(item)

        # Sort descending by cross-encoder score
        reranked.sort(key=lambda x: x["relevance_score"], reverse=True)
        return reranked[:top_k]


reranker_service = RerankerService()


def compute_rrf_scores(
    dense_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    rrf_k: int = 60,
) -> List[Dict[str, Any]]:
    """
    Merge Dense and BM25 results using Reciprocal Rank Fusion (RRF).
    RRF(d) = sum(1 / (k + rank))
    """
    merged_map: Dict[str, Dict[str, Any]] = {}

    for rank, item in enumerate(dense_results, start=1):
        cid = item["chunk_id"]
        if cid not in merged_map:
            merged_map[cid] = {
                "chunk": item,
                "dense_rank": rank,
                "bm25_rank": None,
                "rrf_score": 1.0 / (rrf_k + rank),
            }
        else:
            merged_map[cid]["dense_rank"] = rank
            merged_map[cid]["rrf_score"] += 1.0 / (rrf_k + rank)

    for rank, item in enumerate(bm25_results, start=1):
        cid = item["chunk_id"]
        if cid not in merged_map:
            merged_map[cid] = {
                "chunk": item,
                "dense_rank": None,
                "bm25_rank": rank,
                "rrf_score": 1.0 / (rrf_k + rank),
            }
        else:
            merged_map[cid]["bm25_rank"] = rank
            merged_map[cid]["rrf_score"] += 1.0 / (rrf_k + rank)

    # Sort merged pool by RRF score descending
    sorted_items = sorted(merged_map.values(), key=lambda x: x["rrf_score"], reverse=True)

    candidates = []
    for entry in sorted_items:
        chunk_dict = dict(entry["chunk"])
        chunk_dict["dense_rank"] = entry["dense_rank"]
        chunk_dict["bm25_rank"] = entry["bm25_rank"]
        chunk_dict["rrf_score"] = float(entry["rrf_score"])
        candidates.append(chunk_dict)

    return candidates


def retrieve_context(
    question: str,
    filters: Optional[Dict[str, str]] = None,
    top_k: int = 5,
    dense_k: int = 10,
    bm25_k: int = 10,
    enable_reranker: bool = True,
) -> List[RetrievedChunk]:
    """
    End-to-End Hybrid Retrieval Service:
    1. Dense query encoding -> Qdrant search (top 10)
    2. BM25 tokenized keyword search (top 10)
    3. RRF merge & deduplication -> candidate pool (top 20)
    4. Cross-Encoder reranking -> final top_k passages with verified provenance.
    """
    clean_question = question.strip()
    if not clean_question:
        return []

    logger.info("Executing retrieval for: '%s' (filters=%s, top_k=%d)", clean_question[:60], filters, top_k)

    # 1. Dense Search
    dense_results = []
    try:
        query_vector = embedding_service.encode_query(clean_question)
        dense_results = vector_store.search_dense(
            query_vector=query_vector,
            top_k=dense_k,
            filters=filters,
        )
    except Exception as e:
        logger.error("Dense search failed: %s", e)

    # 2. BM25 Search
    bm25_results = []
    try:
        bm25_results = bm25_service.search(
            query=clean_question,
            top_k=bm25_k,
            filters=filters,
        )
    except Exception as e:
        logger.error("BM25 search failed: %s", e)

    # 3. Reciprocal Rank Fusion
    candidate_pool = compute_rrf_scores(dense_results, bm25_results, rrf_k=60)

    if not candidate_pool:
        logger.warning("No candidates retrieved from either dense or BM25 search.")
        return []

    # 4. Cross-Encoder Reranking
    if enable_reranker and len(candidate_pool) > 1:
        # Pass top candidates (up to 20) to reranker
        to_rerank = candidate_pool[:20]
        final_raw = reranker_service.rerank(clean_question, to_rerank, top_k=top_k)
    else:
        # Fallback to RRF ranking
        final_raw = []
        for cand in candidate_pool[:top_k]:
            item = dict(cand)
            item["relevance_score"] = cand.get("rrf_score", 0.0)
            item["retrieval_method"] = "rrf_fusion"
            final_raw.append(item)

    # 5. Format to typed RetrievedChunk models
    results = []
    for r in final_raw:
        results.append(
            RetrievedChunk(
                chunk_id=r["chunk_id"],
                document_id=r["document_id"],
                document_title=r.get("document_title", "Unknown"),
                source_institution=r.get("source_institution", "ICAR"),
                source_url=r.get("source_url"),
                page_number=r.get("page_number", 1),
                section_heading=r.get("section_heading"),
                text=r.get("text", ""),
                crop_tags=r.get("crop_tags", []),
                topic_tags=r.get("topic_tags", []),
                language=r.get("language", "en"),
                relevance_score=round(r["relevance_score"], 4),
                retrieval_method=r.get("retrieval_method", "hybrid_reranked"),
                dense_rank=r.get("dense_rank"),
                bm25_rank=r.get("bm25_rank"),
                rrf_score=round(r.get("rrf_score", 0.0), 6) if r.get("rrf_score") else None,
            )
        )

    return results
