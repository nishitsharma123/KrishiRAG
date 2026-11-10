from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

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
    page_count: int
    file_path: str
    status: str
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
