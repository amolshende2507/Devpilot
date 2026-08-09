from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from app.db.base_class import Base


class ChatHistory(Base):
    __tablename__ = "chats"

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
    session_id = Column(
        String,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question = Column(
        Text,
        nullable=False
    )
    answer = Column(
        Text,
        nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )