import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    session_id = Column(String(64), nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
