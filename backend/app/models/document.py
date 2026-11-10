import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from backend.app.database.session import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    source_institution = Column(String(255), nullable=True, default="ICAR")
    source_url = Column(String(512), nullable=True)
    publication_date = Column(String(64), nullable=True)
    page_count = Column(Integer, default=0)
    file_path = Column(String(512), nullable=False)
    status = Column(String(64), default="UPLOADED", index=True)  # UPLOADED, PROCESSING, INDEXED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "filename": self.filename,
            "source_institution": self.source_institution,
            "source_url": self.source_url,
            "publication_date": self.publication_date,
            "page_count": self.page_count,
            "file_path": self.file_path,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
