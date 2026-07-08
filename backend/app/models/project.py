from sqlalchemy import Column,String,DateTime,ForeignKey

from datetime import datetime

from uuid import uuid4


from app.db.base import Base



class Project(Base):

    __tablename__="projects"


    id=Column(
        String,
        primary_key=True,
        default=lambda:str(uuid4())
    )


    user_id=Column(
        String,
        ForeignKey("users.id")
    )


    name=Column(
        String
    )


    github_url=Column(
        String
    )


    status=Column(
        String,
        default="pending"
    )


    created_at=Column(
        DateTime,
        default=datetime.utcnow
    )