from pydantic import BaseModel
from typing import List, Dict, Any


class ChatQueryRequest(BaseModel):
    project_id: str
    session_id: str
    question: str


class ChatQueryResponse(BaseModel):
    answer: str
    # Return source documents so the frontend can display file cards (Source Attribution)
    retrieved_sources: List[Dict[str, Any]]