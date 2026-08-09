from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, DateTime, ForeignKey, String
from app.db.base_class import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )
    project_id = Column(
        String,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title = Column(
        String,
        default="New Conversation",
        nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )