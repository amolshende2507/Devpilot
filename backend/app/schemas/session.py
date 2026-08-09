from pydantic import BaseModel
from datetime import datetime


class SessionCreateRequest(BaseModel):
    project_id: str
    title: str = "New Conversation"


class SessionUpdateRequest(BaseModel):
    title: str


class SessionResponse(BaseModel):
    id: str
    project_id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True