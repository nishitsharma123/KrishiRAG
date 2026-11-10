from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class DocumentBase(BaseModel):
    title: str = Field(..., max_length=255, description="Official title of the ICAR or agricultural publication")
    source_institution: Optional[str] = Field("ICAR", max_length=255)
    source_url: Optional[str] = Field(None, max_length=512)
    publication_date: Optional[str] = Field(None, max_length=64)

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: str
    filename: str
    file_hash: Optional[str] = None
    file_size: Optional[int] = 0
    mime_type: Optional[str] = None
    page_count: int
    chunk_count: int = 0
    file_path: str
    status: str
    error_message: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ChunkMetadata(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    source_institution: str
    source_url: Optional[str] = None
    page_number: int
    section_heading: Optional[str] = None
    text: str
    token_count: int
    crop_tags: List[str] = []
    topic_tags: List[str] = []
    language: str = "en"

    model_config = ConfigDict(from_attributes=True)

class DocumentIngestionResult(BaseModel):
    document_id: str
    title: str
    filename: str
    page_count: int
    chunk_count: int
    status: str
    is_duplicate: bool = False
    ocr_pages: List[int] = []
    ocr_errors: List[Dict[str, Any]] = []
    message: str
