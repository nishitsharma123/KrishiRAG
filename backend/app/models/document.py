import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from backend.app.database.session import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for duplicate detection
    file_size = Column(Integer, default=0)  # Size in bytes
    mime_type = Column(String(64), nullable=True)  # application/pdf, text/plain, etc.
    source_institution = Column(String(255), nullable=True, default="ICAR")
    source_url = Column(String(512), nullable=True)
    publication_date = Column(String(64), nullable=True)
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    file_path = Column(String(512), nullable=False)
    status = Column(String(64), default="UPLOADED", index=True)  # UPLOADED, PROCESSING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "filename": self.filename,
            "file_hash": self.file_hash,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "source_institution": self.source_institution,
            "source_url": self.source_url,
            "publication_date": self.publication_date,
            "page_count": self.page_count,
            "chunk_count": self.chunk_count,
            "file_path": self.file_path,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
