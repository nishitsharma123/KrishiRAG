import os
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.health import router as health_router
from backend.app.api.retrieval import router as retrieval_router
from backend.app.api.chat import router as chat_router
from backend.app.api.admin import router as admin_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.database.session import get_db
from backend.app.models.document import Document
from backend.app.schemas.document import DocumentResponse, DocumentIngestionResult
from backend.app.services.ingestion import DocumentIngestionService
from backend.app.utils.chunk_inspector import ChunkInspector
from backend.app.core.config import settings

api_router = APIRouter()

# Include health diagnostics
api_router.include_router(health_router, prefix="")

# Documents Management Router
docs_router = APIRouter(prefix="/documents", tags=["Documents"])

@docs_router.get("", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    """List all registered agricultural documents with their processing status."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [DocumentResponse.model_validate(doc.to_dict()) for doc in docs]

@docs_router.post("/upload", response_model=DocumentIngestionResult, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="PDF, TXT, or DOCX agricultural publication"),
    title: Optional[str] = Form(None, description="Official title of the ICAR publication"),
    source_institution: Optional[str] = Form("ICAR", description="Publishing institute (e.g. ICAR-IARI, PAU, ICAR-CRIDA)"),
    source_url: Optional[str] = Form(None, description="Official verification URL"),
    publication_date: Optional[str] = Form(None, description="Publication year or date"),
    db: Session = Depends(get_db)
):
    """
    Upload and ingest an agricultural document through the end-to-end pipeline:
    Duplicate Check (SHA-256) -> PyMuPDF Page Extraction -> Cleaning -> Heading-Aware Chunking -> Metadata Tagging.
    """
    file_bytes = await file.read()
    result = DocumentIngestionService.ingest_file(
        file_bytes=file_bytes,
        original_filename=file.filename or "uploaded_document.pdf",
        title=title,
        source_institution=source_institution or "ICAR",
        source_url=source_url,
        publication_date=publication_date,
        db=db
    )
    return result

@docs_router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get metadata for a specific document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc.to_dict())

@docs_router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document record, its processed chunks file, and physical storage."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Clean up processed JSON if exists
    proc_path = os.path.join(settings.PROCESSED_DATA_PATH, f"{document_id}.json")
    if os.path.exists(proc_path):
        try:
            os.remove(proc_path)
        except Exception:
            pass

    # Clean up physical storage file if exists
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    db.delete(doc)
    db.commit()
    return {"success": True, "message": f"Document '{doc.title}' deleted successfully."}

@docs_router.get("/{document_id}/chunks")
def inspect_document_chunks(
    document_id: str,
    page: Optional[int] = None,
    tag: Optional[str] = None
):
    """Inspect processed chunks and token statistics for a document."""
    inspection = ChunkInspector.inspect(document_id, page_filter=page, tag_filter=tag)
    if "error" in inspection:
        raise HTTPException(status_code=404, detail=inspection["error"])
    return inspection

api_router.include_router(docs_router)
api_router.include_router(retrieval_router)
api_router.include_router(chat_router)
api_router.include_router(admin_router)
api_router.include_router(evaluation_router)
