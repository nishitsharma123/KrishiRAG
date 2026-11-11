# KrishiRAG (कृषि RAG)

> **Verifiable, Evidence-Grounded Agricultural Advisory Operating System** strictly powered by authentic Indian Council of Agricultural Research (ICAR) publications, State Agricultural Universities (SAUs), and government agricultural guidelines.

---

## 🌾 Overview

KrishiRAG is designed to eliminate agricultural hallucinations. Traditional general-purpose LLMs frequently fabricate pesticide dosages, hallucinate chemical mixtures, or confuse crop diseases, which can lead to crop failures or chemical hazards.

KrishiRAG guarantees that **every agronomic response is directly traceable to verified page numbers and excerpt passages** from authoritative agricultural documents.

### Key Features
- **Strict Evidence Grounding**: Answers only from verified ICAR publications; explicit negative fallback when documentation is silent.
- **Traceable Provenance**: Citation pills linking directly to document title, physical page number, and original context.
- **Resource Efficient**: Engineered for consumer-grade CPU hardware (Ryzen 5 5500U, 8 GB RAM) with embedded in-process vector storage (Qdrant Local) and quantized local LLMs (`qwen3:4b` via Ollama).
- **Hybrid Retrieval**: Multilingual dense embeddings (`intfloat/multilingual-e5-small`) combined with sparse keyword matching (`BM25`) and cross-encoder reranking (`ms-marco-MiniLM-L-6-v2`).

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 19, Vite, Tailwind CSS, Lucide Icons, Axios |
| **Backend** | Python, FastAPI, Pydantic v2, Uvicorn |
| **Database** | SQLite with SQLAlchemy ORM (WAL mode enabled) |
| **Vector Engine** | Qdrant Local Persistent Storage (in-process, zero Docker required) |
| **Embeddings** | `intfloat/multilingual-e5-small` |
| **Reranker** | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| **Document Processing** | PyMuPDF (`fitz`), selective PaddleOCR fallback |
| **Inference Runtime** | Ollama local daemon (`qwen3:4b`) |

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.12+ (or 3.14)
- Node.js 18+ and npm
- Ollama (installed locally)

---

### 2. Ollama Setup & Verification

KrishiRAG utilizes local CPU inference via **Ollama** running the quantized `qwen3:4b` model.

#### A. Installation
- **Windows**: Download and run the installer from the official website: [ollama.com/download/windows](https://ollama.com/download/windows).
- **macOS**: `brew install ollama` or download from [ollama.com/download/mac](https://ollama.com/download/mac).
- **Linux**:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```

#### B. Pull the Required Model
Make sure you have at least ~3.5 GB of free disk space before pulling the model:
```bash
ollama pull qwen3:4b
```

#### C. Start the Ollama Service
On Windows, Ollama typically runs as a background tray icon. If it is not running, start it manually in a dedicated terminal:
```powershell
ollama serve
```

#### D. Verify if Ollama is Running
Check whether the Ollama server is accessible and verify that `qwen3:4b` is installed:

**Option 1: Using the Ollama CLI**
```powershell
# List installed models
ollama list
```
You should see `qwen3:4b` in the output list.

**Option 2: Using curl / PowerShell**
```powershell
# Check server status
curl http://127.0.0.1:11434/api/tags
```
If running, this returns a JSON payload listing available models with HTTP status `200 OK`.

---

### 3. Backend Setup
```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows activation:
.venv\Scripts\activate
# Linux/macOS activation:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Return to root directory
cd ..

# Start backend server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be available at: `http://localhost:8000/docs`

### 4. Frontend Setup
```bash
# In a separate terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend will be accessible at: `http://localhost:5173`

---

## 📁 Repository Structure
```
KrishiRAG/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers & API endpoints
│   │   ├── core/         # Config, logging, error handlers
│   │   ├── database/     # SQLAlchemy engine, session & init
│   │   ├── models/       # ORM entity models
│   │   ├── schemas/      # Pydantic validation schemas
│   │   ├── services/     # Business logic & services
│   │   └── main.py       # Application gateway
│   ├── tests/            # Automated backend tests
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Environment variable template
├── frontend/             # React + Vite + Tailwind CSS client
├── data/
│   ├── raw/              # Raw ICAR PDF documents
│   ├── processed/        # Extracted chunks & indexes
│   └── evaluation/       # Test datasets & RAGAS evaluations
├── storage/              # Local uploaded files & cached assets
├── docs/                 # Documentation & guides
└── tests/                # System-level test suites
```

---

## 📜 Development Status
- [x] **Phase 0**: Environment Inspection and Architecture
- [x] **Phase 1**: Project Foundation (Backend & Frontend Scaffold, Database, Health API)
- [ ] **Phase 2**: Document Ingestion and Processing
- [ ] **Phase 3**: Embeddings, Vector Database, and Hybrid Retrieval
- [ ] **Phase 4**: Qwen3 Integration & Complete RAG Pipeline
- [ ] **Phase 5**: Complete React Frontend & API Integration
- [ ] **Phase 6**: RAG Evaluation and Benchmarking
- [ ] **Phase 7**: Final Optimization and Deployment Preparation
