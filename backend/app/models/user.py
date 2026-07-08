from sqlalchemy import Column, String, DateTime

from datetime import datetime

from uuid import uuid4


from app.db.base import Base



class User(Base):

    __tablename__="users"


    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid4())
    )


    email = Column(
        String,
        unique=True,
        nullable=False
    )


    name = Column(
        String
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )