# KrishiRAG: Technical Decision Records (TDR)

## 1. Context & Architectural Constraints

KrishiRAG is designed to run locally on an AMD Ryzen 5 5500U machine with 8 GB physical RAM and integrated Radeon graphics (sharing ~0.67 GB system memory). The operating environment has 7.33 GB visible RAM, no dedicated GPU (no CUDA), and Windows 11 as the host operating system.

These physical constraints dictate that all architectural choices must optimize for:
1. Low CPU memory footprint (resident set size $\le 4.5$ GB across all processes).
2. Deterministic, hallucination-free retrieval for agricultural safety.
3. Modular separation enabling component replacement without system refactoring.

---

## 2. Architectural Decisions & Tradeoff Analysis

### TDR-01: Vector Database Selection — Qdrant Local Persistent Mode
- **Decision**: Use `qdrant-client` in local persistent storage mode (`path="./data/qdrant_db"`).
- **Alternatives Evaluated**:
  - *Docker-based Qdrant*: Docker Desktop requires WSL2 and consumes 1.5–2.5 GB of RAM idle on Windows, which would immediately starve the 8 GB system.
  - *ChromaDB*: Often exhibits high memory leaks on repeated upserts and SQLite locking issues under concurrent access.
  - *FAISS*: Lacks native persistent metadata filtering and document deletion capabilities out-of-the-box.
- **Rationale**: Qdrant's embedded Python mode runs in-process, saves vectors directly to disk with memory-mapped files (mmap), supports rich payload filtering (`document_id`, `page_number`), and requires 0 GB background container overhead.

---

### TDR-02: Embedding Model — `intfloat/multilingual-e5-small`
- **Decision**: Select `intfloat/multilingual-e5-small` (384 dimensions) with batch size of 8.
- **Alternatives Evaluated**:
  - *multilingual-e5-large / base*: Base (768-dim, ~1.1 GB RAM) and Large (1024-dim, ~2.2 GB RAM) would choke CPU inference latency and exhaust available RAM.
  - *all-MiniLM-L6-v2*: Excellent speed and size (~80 MB), but English-only. Fails on Indian agricultural vernacular (e.g., *kharif*, *khesari*, *arhar*, *mandwa*).
  - *BGE-M3*: Outstanding multilingual retrieval, but model weights (~2.2 GB) and high RAM usage exceed target budget.
- **Rationale**: `multilingual-e5-small` occupies only ~450 MB in memory, performs high-quality cross-lingual retrieval between English and Indian regional terminology, and yields fast CPU vector generation (~30–50 ms per chunk on Ryzen 5 5500U).

---

### TDR-03: Retrieval Strategy — Hybrid (BM25 + Dense) with Reciprocal Rank Fusion (RRF)
- **Decision**: Combine Sparse Lexical Search (Rank-BM25) and Dense Semantic Search (E5 in Qdrant) using Reciprocal Rank Fusion ($k=60$), followed by Cross-Encoder Reranking.
- **Alternatives Evaluated**:
  - *Dense-only Search*: Often misses specific chemical pesticide names (*Emamectin benzoate 5% SG*), pest scientific names (*Helicoverpa armigera*), or exact dosage numbers (*2.5 ml/L*).
  - *Sparse-only (BM25)*: Completely fails when farmers ask colloquial questions (*"how to stop insects eating tomato leaves"*) because the ICAR manual says *"management of leaf miner in Lycopersicon esculentum"*.
- **Rationale**: Hybrid search provides the best of both worlds: dense search handles semantic understanding and vocabulary mismatch, while BM25 ensures exact-match fidelity for chemicals, dosages, and crop varieties.

---

### TDR-04: Reranking Engine — `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Decision**: Use `cross-encoder/ms-marco-MiniLM-L-6-v2` to rerank the top 10 hybrid candidates down to 4–5 final context chunks.
- **Alternatives Evaluated**:
  - *bge-reranker-large*: Demands ~1.5 GB RAM and 400+ ms per candidate pair on CPU.
  - *No Reranker*: Leads to suboptimal context window stuffing, diluting Qwen3's attention and increasing prompt token costs.
- **Rationale**: MiniLM-L-6 Cross-Encoder weights are only ~80 MB (~300 MB resident RAM), evaluating 10 candidates in under 120 ms on 4 CPU threads, while dramatically increasing context relevance.

---

### TDR-05: LLM Selection & Runtime — `qwen3:4b` via Ollama
- **Decision**: Use `qwen3:4b` running through Ollama with `num_ctx: 4096` and `num_thread: 4`.
- **Alternatives Evaluated**:
  - *Llama 3 8B*: Demands 5.5 GB RAM for 4-bit quant, causing instantaneous memory paging and severe system stuttering on an 8 GB laptop.
  - *Qwen2.5 1.5B / Llama 3.2 1B / 3B*: Too small to reliably follow complex citation preservation rules and negative constraints without hallucinating.
  - *Cloud APIs (OpenAI/Anthropic)*: Violates the self-contained, air-gapped, zero-cost local mandate for rural and institutional agricultural deployments.
- **Rationale**: `qwen3:4b` delivers exceptional multilingual reasoning, strict instruction following, and fits neatly into ~2.5 GB RAM, allowing the entire stack to run comfortably within 6 GB total load.

---

### TDR-06: Document Extraction — PyMuPDF with Selective PaddleOCR Fallback
- **Decision**: Use PyMuPDF (`fitz`) as the primary text extractor, checking page text density. If a page has fewer than 50 text characters and contains raster images, trigger PaddleOCR selectively on that single page.
- **Alternatives Evaluated**:
  - *Tesseract OCR on every page*: Extremely slow on CPU (3–8 seconds per page) and unnecessary for high-quality digitally produced ICAR publications.
  - *Unstructured / PyPDF / pdfplumber*: PyMuPDF is 10x faster than pdfplumber in C, has zero Java dependencies, and provides exact character bounding boxes and page indices.
- **Rationale**: 95% of ICAR publications are digital PDFs with native text layers. PyMuPDF extracts text in milliseconds while preserving page boundaries. Selective OCR ensures scanned appendices or circulars are still readable without paying the OCR penalty across whole books.

---

### TDR-07: Application Database — SQLite with SQLAlchemy
- **Decision**: Embedded SQLite (`./data/krishirag.db`) managed via SQLAlchemy ORM.
- **Alternatives Evaluated**:
  - *PostgreSQL*: Requires a standalone service or Docker container, adding background memory overhead.
  - *Pure JSON file storage*: Prone to corruption, lacks transactional integrity, and cannot perform efficient relational lookups between query logs, sessions, and document pages.
- **Rationale**: SQLite is zero-overhead, crash-resilient (WAL mode enabled), acid-compliant, and perfectly suited for single-tenant local agricultural advisory systems.

---

### TDR-08: Python Runtime & Dependency Compatibility
- **Decision**: Use Python 3.12 as the target for virtual environment creation if Python 3.14 encounters wheel availability issues for PyTorch/PaddleOCR.
- **Rationale**: While Python 3.14.5 is the current system default, Python 3.12 is already installed on the machine (`C:\Users\mindg\AppData\Local\Programs\Python\Python312`) and provides 100% pre-compiled binary wheel support for `torch`, `sentence-transformers`, `scipy`, and `onnxruntime`.

---

## 3. System Memory Budget Breakdown (8 GB RAM)

| Subsystem | Peak RAM Budget | Mitigation Mechanism |
| :--- | :--- | :--- |
| **Windows OS + Essential Services** | 2.5 GB | Base system operating footprint |
| **Ollama Service (`qwen3:4b`)** | 2.6 GB | Thread limit = 4, Context = 4096 |
| **FastAPI Backend + Uvicorn** | 0.2 GB | Lightweight async event loop |
| **Qdrant Vector DB (Embedded)** | 0.3 GB | Memory-mapped on-disk storage |
| **Embedding Engine (Batch Ingest)** | 0.4 GB | Loaded only during ingestion or sequential inference |
| **Cross-Encoder Reranker** | 0.3 GB | Inferred sequentially, memory cleared via `gc.collect()` |
| **Frontend (Browser tab)** | 0.5 GB | Optimized bundle, minimal React state |
| **Total Peak Operational RAM** | **~6.8 GB** | **Leaves ~0.5 - 1.0 GB headroom against thrashing** |
