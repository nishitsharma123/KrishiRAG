"""
Retrieval & Indexing Integration Tests — Phase 3
Tests dense retrieval, BM25 keyword search, RRF fusion, Cross-Encoder reranking,
and verifies accuracy across authentic ICAR agricultural queries.
"""

import os
import pytest
from backend.app.services.vector_store import vector_store
from backend.app.services.bm25_service import bm25_service
from backend.app.services.retrieval_service import retrieve_context, compute_rrf_scores


@pytest.fixture(scope="module")
def setup_indexes():
    """Ensure indexes are loaded."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    bm25_service.load_index()


def test_vector_store_collection_stats(setup_indexes):
    """Verify Qdrant collection is created and holds vectors."""
    stats = vector_store.get_collection_stats()
    assert "error" not in stats
    assert stats["points_count"] > 0
    assert stats["collection_name"] == "icar_agricultural_knowledge"


def test_bm25_service_status(setup_indexes):
    """Verify BM25 index is built and contains chunk vocabulary."""
    stats = bm25_service.get_stats()
    assert stats["indexed_chunks"] > 0
    assert stats["is_loaded"] is True


def test_bm25_exact_agricultural_term_search(setup_indexes):
    """Verify BM25 correctly matches key agricultural terminology."""
    queries = ["wheat", "paddy", "nitrogen", "phosphorus", "potassium", "rust", "aphid"]
    for q in queries:
        results = bm25_service.search(q, top_k=5)
        assert len(results) > 0, f"BM25 should return results for core agricultural term: {q}"
        assert any(q in r["text"].lower() for r in results)


def test_rrf_fusion_logic():
    """Verify Reciprocal Rank Fusion computes correct deterministic ranks."""
    dense = [
        {"chunk_id": "c1", "text": "wheat seed rate 100 kg"},
        {"chunk_id": "c2", "text": "nitrogen application"},
    ]
    bm25 = [
        {"chunk_id": "c2", "text": "nitrogen application"},
        {"chunk_id": "c3", "text": "irrigation schedule"},
    ]
    candidates = compute_rrf_scores(dense, bm25, rrf_k=60)
    assert len(candidates) == 3
    # c2 appeared in both (rank 2 in dense, rank 1 in bm25) -> should have highest RRF score
    assert candidates[0]["chunk_id"] == "c2"
    assert candidates[0]["dense_rank"] == 2
    assert candidates[0]["bm25_rank"] == 1


def test_retrieve_context_returns_citation_metadata(setup_indexes):
    """Verify retrieve_context returns all citation-traceable fields."""
    question = "What is the recommended fertilizer dose for wheat?"
    results = retrieve_context(question, top_k=3, enable_reranker=True)

    assert len(results) > 0
    for chunk in results:
        assert chunk.chunk_id is not None
        assert chunk.document_id is not None
        assert chunk.document_title is not None
        assert chunk.page_number >= 1
        assert len(chunk.text) > 20
        assert chunk.relevance_score is not None
        assert chunk.retrieval_method in ("hybrid_reranked", "rrf_fusion")


def test_filtered_retrieval(setup_indexes):
    """Verify retrieval filters restrict results to targeted crops/topics."""
    results = retrieve_context(
        question="disease management in wheat",
        filters={"crop": "Wheat"},
        top_k=5,
    )
    if results:
        # All returned chunks must have 'Wheat' in crop_tags
        for r in results:
            assert "Wheat" in r.crop_tags
