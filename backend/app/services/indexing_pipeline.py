"""
Indexing Pipeline Service — Phase 3
Coordinates embedding generation, Qdrant vector upsert, and BM25 indexing
for all processed agricultural document chunks.
"""

from __future__ import annotations

import glob
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings
from backend.app.services.embedding_service import embedding_service
from backend.app.services.vector_store import vector_store
from backend.app.services.bm25_service import bm25_service

logger = logging.getLogger(__name__)


class IndexingPipeline:
    """Manages batch embedding generation and unified index creation."""

    @classmethod
    def index_all_documents(
        cls,
        processed_dir: Optional[str] = None,
        force_rebuild: bool = False,
    ) -> Dict[str, Any]:
        """
        Process all JSON chunk files in data/processed:
        1. Initialize Qdrant collection if not present
        2. Read all chunks
        3. Batch encode passages with multilingual-e5-small
        4. Upsert vectors and payloads into Qdrant
        5. Build and persist BM25 index
        """
        start_time = time.time()
        p_dir = processed_dir or settings.PROCESSED_DATA_PATH
        json_files = glob.glob(os.path.join(p_dir, "*.json"))

        logger.info("Starting indexing pipeline over %d files in %s...", len(json_files), p_dir)

        # 1. Ensure Qdrant collection exists
        vector_store.initialize_collection()

        # 2. Gather all chunks
        all_chunks: List[Dict[str, Any]] = []
        doc_count = 0

        for fpath in json_files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                chunks = data.get("chunks", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                if chunks:
                    all_chunks.extend(chunks)
                    doc_count += 1
            except Exception as e:
                logger.error("Failed to read processed chunk file %s: %s", fpath, e)

        if not all_chunks:
            return {
                "status": "empty",
                "message": "No processed chunks found to index.",
                "total_documents": 0,
                "total_chunks": 0,
                "duration_seconds": round(time.time() - start_time, 2),
            }

        print(f"Collected {len(all_chunks)} chunks across {doc_count} documents.", flush=True)

        # 3. Dense Embeddings
        texts = [c.get("text", "") for c in all_chunks]
        print(f"Computing embeddings for {len(texts)} chunks...", flush=True)
        embeddings = embedding_service.encode_passages(texts)
        print(f"Embeddings generated with shape: {embeddings.shape}", flush=True)

        # 4. Upsert to Qdrant
        print("Upserting vectors into Qdrant...", flush=True)
        if force_rebuild:
            indexed_vectors = vector_store.rebuild_index(all_chunks, embeddings)
        else:
            indexed_vectors = vector_store.upsert_chunks(all_chunks, embeddings)
        print(f"Upserted {indexed_vectors} vectors into Qdrant.", flush=True)

        # 5. Build BM25 index
        print("Building BM25 index...", flush=True)
        bm25_count = bm25_service.build_index(p_dir)
        print(f"BM25 indexed {bm25_count} chunks.", flush=True)

        duration = round(time.time() - start_time, 2)
        logger.info(
            "Indexing complete: %d chunks embedded & indexed in Qdrant, %d in BM25 in %.2fs",
            indexed_vectors,
            bm25_count,
            duration,
        )

        return {
            "status": "success",
            "total_documents": doc_count,
            "total_chunks": len(all_chunks),
            "qdrant_points": indexed_vectors,
            "bm25_chunks": bm25_count,
            "duration_seconds": duration,
        }

    @classmethod
    def index_single_document(cls, document_id: str) -> Dict[str, Any]:
        """Index chunks from a single newly-processed document."""
        p_dir = settings.PROCESSED_DATA_PATH
        fpath = os.path.join(p_dir, f"{document_id}.json")
        if not os.path.exists(fpath):
            raise FileNotFoundError(f"Processed file not found: {fpath}")

        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        chunks = data.get("chunks", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        if not chunks:
            return {"status": "empty", "chunks_indexed": 0}

        vector_store.initialize_collection()
        texts = [c.get("text", "") for c in chunks]
        embeddings = embedding_service.encode_passages(texts)
        upserted = vector_store.upsert_chunks(chunks, embeddings)

        # Rebuild BM25 to include the new document
        bm25_service.build_index(p_dir)

        return {
            "status": "success",
            "document_id": document_id,
            "chunks_indexed": upserted,
        }
