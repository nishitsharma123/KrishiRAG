"""
BM25 Service — Phase 3
BM25 keyword search index built over all processed chunk texts.

Preserves exact agricultural terminology:
- Scientific names (Puccinia striiformis, Xanthomonas oryzae, etc.)
- Specific chemical active ingredients (pendimethalin, chlorpyrifos, carbendazim)
- Cultivar names (HD 2967, PBW 343, Pusa Basmati 1121)
- Nutrient formulations (NPK 120:60:40, urea, DAP, MOP)
"""

from __future__ import annotations

import glob
import json
import logging
import os
import pickle
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

INDEX_CACHE_PATH = os.path.join("data", "processed", "bm25_index.pkl")


def tokenize_agricultural_text(text: str) -> List[str]:
    """
    Tokenize text preserving agricultural hyphenated terms, ratios, and alphanumeric codes.
    E.g. 'NPK 120:60:40', 'HD-2967', '2,4-D', 'ZnSO4'.
    """
    if not text:
        return []
    # Lowercase but preserve dashes and colons within words/numbers
    text_clean = text.lower()
    # Replace disruptive punctuation except hyphens, dots, and colons in numbers/terms
    tokens = re.findall(r"[a-z0-9]+(?:[-:_/.][a-z0-9]+)*", text_clean)
    return tokens


class BM25Service:
    """In-memory BM25 index with disk persistence for instant re-loads."""

    _instance: Optional["BM25Service"] = None

    def __new__(cls) -> "BM25Service":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._bm25 = None
            cls._instance._corpus_chunks: List[Dict[str, Any]] = []
            cls._instance._chunk_id_to_idx: Dict[str, int] = {}
        return cls._instance

    def is_indexed(self) -> bool:
        return self._bm25 is not None and len(self._corpus_chunks) > 0

    def get_stats(self) -> Dict[str, Any]:
        return {
            "indexed_chunks": len(self._corpus_chunks),
            "is_loaded": self._bm25 is not None,
            "cache_file_exists": os.path.exists(INDEX_CACHE_PATH),
        }

    def build_index(self, processed_dir: str = os.path.join("data", "processed")) -> int:
        """
        Scan all processed JSON documents in data/processed, tokenize text,
        and construct the BM25Okapi index.
        """
        from rank_bm25 import BM25Okapi

        json_files = glob.glob(os.path.join(processed_dir, "*.json"))
        logger.info("Building BM25 index from %d processed document files...", len(json_files))

        all_chunks: List[Dict[str, Any]] = []
        tokenized_corpus: List[List[str]] = []

        for fpath in json_files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                chunks = data.get("chunks", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                for chunk in chunks:
                    text = chunk.get("text", "")
                    tokens = tokenize_agricultural_text(text)
                    if tokens:
                        all_chunks.append(chunk)
                        tokenized_corpus.append(tokens)
            except Exception as e:
                logger.warning("Failed to read processed file for BM25: %s (%s)", fpath, e)

        if not tokenized_corpus:
            logger.warning("No chunks found to index for BM25.")
            return 0

        self._bm25 = BM25Okapi(tokenized_corpus)
        self._corpus_chunks = all_chunks
        self._chunk_id_to_idx = {c["chunk_id"]: i for i, c in enumerate(all_chunks)}

        # Persist to disk
        try:
            os.makedirs(os.path.dirname(INDEX_CACHE_PATH), exist_ok=True)
            with open(INDEX_CACHE_PATH, "wb") as f:
                pickle.dump({
                    "bm25": self._bm25,
                    "corpus_chunks": self._corpus_chunks,
                    "chunk_id_to_idx": self._chunk_id_to_idx,
                }, f)
            logger.info("BM25 index saved to %s (%d chunks)", INDEX_CACHE_PATH, len(all_chunks))
        except Exception as e:
            logger.error("Failed to persist BM25 cache: %s", e)

        return len(all_chunks)

    def load_index(self) -> bool:
        """Load precomputed BM25 index from disk cache."""
        if os.path.exists(INDEX_CACHE_PATH):
            try:
                with open(INDEX_CACHE_PATH, "rb") as f:
                    data = pickle.load(f)
                self._bm25 = data["bm25"]
                self._corpus_chunks = data["corpus_chunks"]
                self._chunk_id_to_idx = data["chunk_id_to_idx"]
                logger.info("Loaded BM25 index from cache (%d chunks)", len(self._corpus_chunks))
                return True
            except Exception as e:
                logger.warning("Failed to load BM25 cache: %s", e)
        return False

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search the BM25 index and return the top-k chunks.
        Optionally apply filters (crop, topic, institution, document_id).
        """
        if self._bm25 is None:
            if not self.load_index():
                self.build_index()

        if self._bm25 is None or not self._corpus_chunks:
            return []

        query_tokens = tokenize_agricultural_text(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)

        # Pair scores with chunk objects
        scored_results = []
        for i, score in enumerate(scores):
            if score <= 0.0:
                continue
            chunk = self._corpus_chunks[i]

            # Apply filters if provided
            if filters:
                if filters.get("crop") and filters["crop"] not in chunk.get("crop_tags", []):
                    continue
                if filters.get("topic") and filters["topic"] not in chunk.get("topic_tags", []):
                    continue
                if filters.get("institution") and filters["institution"] != chunk.get("source_institution"):
                    continue
                if filters.get("document_id") and filters["document_id"] != chunk.get("document_id"):
                    continue

            scored_results.append((score, chunk))

        # Sort descending by BM25 score
        scored_results.sort(key=lambda x: x[0], reverse=True)
        top_results = scored_results[:top_k]

        return [
            {
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "document_title": chunk.get("document_title", ""),
                "source_institution": chunk.get("source_institution", ""),
                "source_url": chunk.get("source_url", ""),
                "page_number": chunk.get("page_number", 0),
                "section_heading": chunk.get("section_heading", ""),
                "text": chunk.get("text", ""),
                "crop_tags": chunk.get("crop_tags", []),
                "topic_tags": chunk.get("topic_tags", []),
                "language": chunk.get("language", "en"),
                "bm25_score": float(score),
                "retrieval_method": "bm25",
            }
            for score, chunk in top_results
        ]


# Module-level singleton
bm25_service = BM25Service()
