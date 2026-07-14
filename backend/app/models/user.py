from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, DateTime, String
from app.db.base_class import Base # <-- UPDATED

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))