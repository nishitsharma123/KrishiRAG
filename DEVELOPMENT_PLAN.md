# KrishiRAG: Master Development Plan

## Phase Overview & Execution Strategy

KrishiRAG is structured into eight sequential phases. Each phase is independent, verifiable, and must satisfy strict completion criteria before progressing to the next.

```mermaid
graph LR
    P0["Phase 0: Environment & Architecture"] --> P1["Phase 1: Project Foundation"]
    P1 --> P2["Phase 2: Ingestion & Processing"]
    P2 --> P3["Phase 3: Embeddings & Retrieval"]
    P3 --> P4["Phase 4: LLM & RAG Pipeline"]
    P4 --> P5["Phase 5: Frontend & Integration"]
    P5 --> P6["Phase 6: Evaluation & Testing"]
    P6 --> P7["Phase 7: Optimization & Deployment"]
```

---

## Detailed Phase Breakdown

### Phase 0: Environment Inspection & Architecture (Current Phase)
- **Objective**: Audit host environment, identify hardware and software constraints, verify tooling availability, and establish the technical blueprints.
- **Key Deliverables**:
  - Audit report on Python, Node, RAM, Disk, Ollama, Docker, Git.
  - `PROJECT_ARCHITECTURE.md`: Complete system topology and data flows.
  - `DEVELOPMENT_PLAN.md`: Phase-by-phase implementation roadmap.
  - `TECHNICAL_DECISIONS.md`: Justification of technology choices and performance tradeoffs.
- **Verification Gate**: User approval of Phase 0 audit and architecture blueprints.

---

### Phase 1: Project Foundation & Backend/Frontend Setup
- **Objective**: Initialize clean repository structure, virtual environments, dependency manifests, configuration system, and basic health-check services.
- **Tasks**:
  1. Initialize Git repository with complete `.gitignore`.
  2. Setup isolated Python virtual environment (`.venv`) and configure package installer.
  3. Create modular FastAPI backend folder hierarchy (`app/core/`, `app/api/`, `app/services/`, `app/models/`, `app/schemas/`).
  4. Implement `pydantic-settings` environment configuration with defaults for all model names and paths.
  5. Setup SQLite database via SQLAlchemy with initial migrations/tables.
  6. Bootstrap React 19 + Vite + Tailwind CSS frontend under `frontend/`.
  7. Implement backend `/health` endpoint and verify frontend-to-backend communication.
- **Verification Gate**: Automated test passing for `/health` and backend startup verification.

---

### Phase 2: Document Ingestion & Processing
- **Objective**: Implement robust ICAR PDF extraction, page tracking, text normalization, and semantic chunking.
- **Tasks**:
  1. Build `PDFExtractor` using PyMuPDF (`fitz`), guaranteeing 100% preservation of page numbers.
  2. Implement scan-detection logic with selective PaddleOCR fallback for image-only pages.
  3. Implement `AgronomicTextCleaner` to sanitize headers, footers, and strange whitespace while preserving chemical formulas, dosages, and pest names.
  4. Implement `SlidingWindowChunker` (500–700 tokens, 80-token overlap) attaching metadata (`doc_id`, `doc_title`, `page_number`, `chunk_index`).
  5. Save processed chunks and metadata into SQLite database.
  6. Ingest at least one authentic ICAR agricultural publication.
- **Verification Gate**: Unit tests verifying chunk bounds, token counts, and 100% page-number fidelity across sample documents.

---

### Phase 3: Embeddings, Vector Database, and Retrieval
- **Objective**: Setup Qdrant local storage, multilingual E5 embeddings, BM25 indexing, and hybrid retrieval with reranking.
- **Tasks**:
  1. Configure `QdrantClient` in persistent local directory mode (`./data/qdrant_db`).
  2. Implement `EmbeddingService` wrapping `intfloat/multilingual-e5-small` with batch processing (batch size = 8).
  3. Implement `BM25IndexService` for tokenized agricultural keyword retrieval.
  4. Build hybrid retrieval combining Top-10 Dense + Top-10 Sparse candidates using Reciprocal Rank Fusion (RRF, $k=60$).
  5. Implement `RerankerService` using `cross-encoder/ms-marco-MiniLM-L-6-v2` returning the top 4–5 reranked chunks.
- **Verification Gate**: Automated test evaluating retrieval recall and ranking order on agricultural test queries (*e.g., "wheat yellow rust treatment", "urea dosage for paddy"*).

---

### Phase 4: Qwen3 Integration & Complete RAG Pipeline
- **Objective**: Integrate Ollama `qwen3:4b`, build strict evidence-grounded prompt templates, and enforce citation verification.
- **Tasks**:
  1. Build `OllamaClient` with configurable timeout, context length (4096), and thread control (4 threads).
  2. Implement `RAGPromptEngine` injecting retrieved context with explicit `[Doc: X, Page: Y]` tags.
  3. Formulate strict system instructions prohibiting unverified recommendations and enforcing standard fallback phrases when context is insufficient.
  4. Build `CitationValidator` verifying that every citation in the response corresponds to actual context chunks.
  5. Expose `/api/v1/query` endpoint with streaming and non-streaming response modes.
- **Verification Gate**: Automated integration test verifying answer relevance, citation validity, and zero-hallucination behavior.

---

### Phase 5: Complete React Frontend & API Integration
- **Objective**: Build a modern, responsive user interface connecting document ingestion, search, chat, and citation verification.
- **Tasks**:
  1. Implement Document Management view: PDF upload, extraction progress bar, indexed document list.
  2. Implement Advisory Chat view: Streaming response display, query suggestions, clean markdown rendering.
  3. Implement Citation Sidecar: Interactive drawer displaying source document title, page number, and highlighted excerpt when clicking a citation.
  4. Implement error boundaries, loading skeletons, and empty states.
  5. Connect frontend to FastAPI backend using typed API client.
- **Verification Gate**: End-to-end user workflow test: Upload PDF $\rightarrow$ Index $\rightarrow$ Ask question $\rightarrow$ Inspect citation.

---

### Phase 6: RAG Evaluation & Testing
- **Objective**: Measure retrieval precision, answer faithfulness, and citation accuracy using automated benchmarks and RAGAS.
- **Tasks**:
  1. Curate agricultural QA evaluation dataset (ground-truth question, ICAR source document, expected page, reference answer).
  2. Implement custom evaluation harness measuring:
     - Context Recall (Hit Rate @ 5)
     - Context Precision (Mean Reciprocal Rank)
     - Faithfulness / Citation Precision (% of statements backed by context)
  3. Run automated RAGAS assessment suite.
  4. Generate formal evaluation report with metrics table.
- **Verification Gate**: Faithfulness score $\ge 90\%$, citation precision $\ge 95\%$.

---

### Phase 7: Final Integration, Optimization & Deployment Preparation
- **Objective**: Resource profiling, memory leak verification, cache optimization, startup scripts, and final documentation.
- **Tasks**:
  1. Profile memory consumption under sustained load on 8 GB RAM.
  2. Implement single-command startup script (`start_krishirag.bat` / PowerShell).
  3. Complete user guide, API documentation, and architecture handoff.
  4. Final end-to-end regression testing.
- **Verification Gate**: Clean execution within 8 GB RAM envelope with no memory leaks or process crashes.
