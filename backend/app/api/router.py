from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.api.health import router as health_router
from backend.app.database.session import get_db
from backend.app.models.document import Document
from backend.app.schemas.document import DocumentResponse

api_router = APIRouter()

# Include health endpoints under /api
api_router.include_router(health_router, prefix="")

# Provide document retrieval endpoint
docs_router = APIRouter(prefix="/documents", tags=["Documents"])

@docs_router.get("", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    """List all registered agricultural documents."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [DocumentResponse.model_validate(doc.to_dict()) for doc in docs]

api_router.include_router(docs_router)
