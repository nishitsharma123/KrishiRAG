"""
Embedding Service — Phase 3
Wraps intfloat/multilingual-e5-small for passage and query encoding.

Design decisions:
- Singleton pattern with lazy loading: model is loaded only when first needed.
- CPU-only inference to stay within 8 GB RAM constraint.
- E5 prefix protocol: 'passage: ' for indexing, 'query: ' for retrieval.
- Normalize embeddings to unit L2 norm for cosine similarity via dot product.
- Batch size capped at EMBEDDING_BATCH_SIZE (default 8) to bound peak RAM.
- Explicit unload() method releases model weights after bulk ingestion.
"""

from __future__ import annotations

import logging
import gc
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Singleton wrapper around multilingual-e5-small."""

    _instance: Optional["EmbeddingService"] = None
    _model = None  # sentence_transformers.SentenceTransformer

    # E5 model prefixes — required for correct retrieval quality
    PASSAGE_PREFIX = "passage: "
    QUERY_PREFIX = "query: "

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    # Model lifecycle
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """Load the embedding model into memory (only once)."""
        if self._model is not None:
            return

        from sentence_transformers import SentenceTransformer
        from backend.app.core.config import settings

        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL_NAME)
        try:
            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL_NAME,
                device="cpu",
                local_files_only=True,
            )
        except Exception:
            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL_NAME,
                device="cpu",
            )
        logger.info(
            "Embedding model loaded. Max sequence length: %d",
            self._model.max_seq_length,
        )

    def unload(self) -> None:
        """Release model weights to free RAM after bulk ingestion."""
        if self._model is not None:
            logger.info("Unloading embedding model to free RAM.")
            del self._model
            self._model = None
            gc.collect()

    # ------------------------------------------------------------------
    # Encoding API
    # ------------------------------------------------------------------

    def encode_passages(self, texts: List[str]) -> np.ndarray:
        """
        Encode a list of passage strings for vector database indexing.

        Applies 'passage: ' prefix, batches at EMBEDDING_BATCH_SIZE,
        and returns L2-normalised float32 embeddings of shape (N, 384).
        """
        self._load_model()

        from backend.app.core.config import settings

        prefixed = [self.PASSAGE_PREFIX + t for t in texts]
        batch_size = settings.EMBEDDING_BATCH_SIZE

        embeddings = self._model.encode(
            prefixed,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
        return embeddings.astype(np.float32)

    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a single user query for vector similarity search.

        Applies 'query: ' prefix and returns L2-normalised float32
        embedding of shape (384,).
        """
        self._load_model()

        prefixed = self.QUERY_PREFIX + query
        embedding = self._model.encode(
            [prefixed],
            batch_size=1,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embedding[0].astype(np.float32)

    def get_embedding_dimension(self) -> int:
        """Return the vector dimension of the loaded model (384 for e5-small)."""
        self._load_model()
        return self._model.get_sentence_embedding_dimension()


# Module-level singleton access
embedding_service = EmbeddingService()
