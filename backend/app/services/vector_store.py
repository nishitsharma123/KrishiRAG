"""
Vector Store Service — Phase 3
Manages Qdrant local persistent storage for agricultural knowledge embeddings.

Design decisions:
- In-process Qdrant (QdrantClient(path=...)) — no Docker required.
- Collection auto-created on first call with COSINE distance metric.
- chunk_id is used as the Qdrant point UUID (deterministic, dedup-safe).
- Full payload stored per point for citation-ready retrieval without DB roundtrips.
- Batch upsert in groups of 64 to bound memory per operation.
- Payload filter support for crop / topic / institution / document_id.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


def _chunk_id_to_uuid(chunk_id: str) -> str:
    """Convert an arbitrary chunk_id string to a stable UUID v5."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))


class VectorStore:
    """Singleton wrapper around QdrantClient for the ICAR knowledge collection."""

    _instance: Optional["VectorStore"] = None
    _client = None

    def __new__(cls) -> "VectorStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    # Client lifecycle
    # ------------------------------------------------------------------

    def _get_client(self):
        """Return (or lazily create) the persistent Qdrant client."""
        if self._client is not None:
            return self._client

        from qdrant_client import QdrantClient
        from backend.app.core.config import settings

        logger.info("Opening Qdrant local storage at: %s", settings.QDRANT_STORAGE_PATH)
        self._client = QdrantClient(path=settings.QDRANT_STORAGE_PATH)
        return self._client

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def initialize_collection(self) -> Dict[str, Any]:
        """
        Ensure the ICAR knowledge collection exists with the correct
        vector dimensions and distance metric.  Safe to call multiple times.
        """
        from qdrant_client.models import Distance, VectorParams
        from backend.app.core.config import settings

        client = self._get_client()
        collection_name = settings.QDRANT_COLLECTION_NAME
        vector_size = 384  # multilingual-e5-small output dimension

        existing = [c.name for c in client.get_collections().collections]
        if collection_name not in existing:
            logger.info("Creating Qdrant collection: %s", collection_name)
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info("Collection created successfully.")
        else:
            logger.info("Collection '%s' already exists.", collection_name)

        return self.get_collection_stats()

    def get_collection_stats(self) -> Dict[str, Any]:
        """Return vector count and segment info for the collection."""
        from backend.app.core.config import settings

        client = self._get_client()
        try:
            info = client.get_collection(settings.QDRANT_COLLECTION_NAME)
            pts = getattr(info, "points_count", 0)
            vecs = getattr(info, "vectors_count", pts)
            opt_status = "unknown"
            if hasattr(info, "optimizer_status") and info.optimizer_status:
                opt_status = getattr(info.optimizer_status, "status", str(info.optimizer_status))
            return {
                "collection_name": settings.QDRANT_COLLECTION_NAME,
                "vectors_count": vecs,
                "points_count": pts,
                "status": str(getattr(info, "status", "ready")),
                "optimizer_status": str(opt_status),
            }
        except Exception as exc:
            logger.error("Failed to get collection stats: %s", exc)
            return {"error": str(exc)}

    def collection_exists(self) -> bool:
        """Check if the ICAR collection has been created."""
        from backend.app.core.config import settings

        client = self._get_client()
        existing = [c.name for c in client.get_collections().collections]
        return settings.QDRANT_COLLECTION_NAME in existing

    # ------------------------------------------------------------------
    # Upsert
    # ------------------------------------------------------------------

    def upsert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: np.ndarray,
        batch_size: int = 64,
    ) -> int:
        """
        Upsert chunk embeddings and payloads into Qdrant.

        Each chunk dict must contain the full metadata set produced by Phase 2
        (chunk_id, document_id, document_title, source_institution, source_url,
        page_number, section_heading, text, crop_tags, topic_tags, language).

        Returns the number of points upserted.
        """
        from qdrant_client.models import PointStruct
        from backend.app.core.config import settings

        client = self._get_client()
        collection_name = settings.QDRANT_COLLECTION_NAME

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"chunks ({len(chunks)}) and embeddings ({len(embeddings)}) must have the same length"
            )

        points = []
        for chunk, vector in zip(chunks, embeddings):
            point_id = _chunk_id_to_uuid(chunk["chunk_id"])
            payload = {
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "document_title": chunk.get("document_title", ""),
                "source_institution": chunk.get("source_institution", ""),
                "source_url": chunk.get("source_url") or "",
                "page_number": chunk.get("page_number", 0),
                "section_heading": chunk.get("section_heading", ""),
                "text": chunk.get("text", ""),
                "crop_tags": chunk.get("crop_tags", []),
                "topic_tags": chunk.get("topic_tags", []),
                "language": chunk.get("language", "en"),
            }
            points.append(PointStruct(id=point_id, vector=vector.tolist(), payload=payload))

        total = 0
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            client.upsert(collection_name=collection_name, points=batch)
            total += len(batch)
            logger.debug("Upserted batch %d–%d", i, i + len(batch))

        logger.info("Upserted %d points into '%s'.", total, collection_name)
        return total

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_dense(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filters: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform dense vector search.  Returns up to top_k results.

        filters: optional dict with keys from {crop, topic, institution, document_id}.
        Each active key is ANDed as a payload match condition.
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        from backend.app.core.config import settings

        client = self._get_client()

        qdrant_filter = None
        if filters:
            conditions = []
            if filters.get("crop"):
                conditions.append(
                    FieldCondition(key="crop_tags", match=MatchValue(value=filters["crop"]))
                )
            if filters.get("topic"):
                conditions.append(
                    FieldCondition(key="topic_tags", match=MatchValue(value=filters["topic"]))
                )
            if filters.get("institution"):
                conditions.append(
                    FieldCondition(
                        key="source_institution",
                        match=MatchValue(value=filters["institution"]),
                    )
                )
            if filters.get("document_id"):
                conditions.append(
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=filters["document_id"]),
                    )
                )
            if conditions:
                qdrant_filter = Filter(must=conditions)

        if hasattr(client, "query_points"):
            res = client.query_points(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query=query_vector.tolist(),
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
            )
            results = res.points if hasattr(res, "points") else res
        else:
            results = client.search(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_vector=query_vector.tolist(),
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
            )

        return [
            {
                "chunk_id": r.payload.get("chunk_id"),
                "document_id": r.payload.get("document_id"),
                "document_title": r.payload.get("document_title"),
                "source_institution": r.payload.get("source_institution"),
                "source_url": r.payload.get("source_url"),
                "page_number": r.payload.get("page_number"),
                "section_heading": r.payload.get("section_heading"),
                "text": r.payload.get("text"),
                "crop_tags": r.payload.get("crop_tags", []),
                "topic_tags": r.payload.get("topic_tags", []),
                "language": r.payload.get("language", "en"),
                "dense_score": r.score,
                "retrieval_method": "dense",
            }
            for r in results
        ]

    # ------------------------------------------------------------------
    # Deletion
    # ------------------------------------------------------------------

    def delete_document(self, document_id: str) -> int:
        """
        Delete all Qdrant points belonging to a document.
        Returns the number of points deleted (approximate from stats diff).
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        from backend.app.core.config import settings

        client = self._get_client()
        before = self.get_collection_stats().get("points_count", 0)

        client.delete(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id", match=MatchValue(value=document_id)
                    )
                ]
            ),
        )

        after = self.get_collection_stats().get("points_count", 0)
        deleted = (before or 0) - (after or 0)
        logger.info("Deleted ~%d points for document_id=%s", deleted, document_id)
        return deleted

    def rebuild_index(self, all_chunks: List[Dict[str, Any]], embeddings: np.ndarray) -> int:
        """
        Clear the entire collection and re-index from scratch.
        Used when a full reindex is explicitly requested.
        """
        from backend.app.core.config import settings

        client = self._get_client()
        logger.warning("Rebuilding entire Qdrant index — deleting all points.")
        client.delete_collection(settings.QDRANT_COLLECTION_NAME)
        self.initialize_collection()
        return self.upsert_chunks(all_chunks, embeddings)


# Module-level singleton
vector_store = VectorStore()
