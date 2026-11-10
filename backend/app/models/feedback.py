import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    rating = Column(Integer, nullable=False)  # 1 to 5, or 1/-1 for thumbs
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    message = relationship("Message", back_populates="feedback")

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
