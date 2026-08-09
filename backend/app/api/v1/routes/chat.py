from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.schemas.session import SessionCreateRequest, SessionUpdateRequest, SessionResponse
from app.services.ai_service import AIService
from app.core.security import verify_token
from app.models.chat import ChatHistory
from app.models.chat_session import ChatSession

router = APIRouter(
    prefix="/chat",
    tags=["AI Code Chat & Sessions"]
)


# ============================================================================
# SESSION CRUD OPERATIONS
# ============================================================================

@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_chat_session(
    data: SessionCreateRequest,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(verify_token)
):
    """Creates a new isolated chat thread for a specific project."""
    session = ChatSession(
        project_id=data.project_id,
        title=data.title
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get(
    "/project/{project_id}/sessions",
    response_model=list[SessionResponse],
    status_code=status.HTTP_200_OK
)
def list_project_sessions(
    project_id: str,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(verify_token)
):
    """Retrieves all chat sessions for a project sorted by newest first."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.project_id == project_id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return sessions


@router.put(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK
)
def update_chat_session_title(
    session_id: str,
    data: SessionUpdateRequest,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(verify_token)
):
    """Renames an existing chat session."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    
    session.title = data.title
    db.commit()
    db.refresh(session)
    return session


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(verify_token)
):
    """Deletes a chat session and cascade-deletes all associated messages."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    
    db.delete(session)
    db.commit()
    return None


# ============================================================================
# MESSAGE HISTORY & QUERY ENGINE
# ============================================================================

@router.get(
    "/sessions/{session_id}/messages",
    status_code=status.HTTP_200_OK
)
def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(verify_token)
):
    """Retrieves the chronological message timeline for a specific session."""
    chats = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )

    messages = []
    for chat in chats:
        messages.append({"role": "user", "content": chat.question})
        messages.append({"role": "assistant", "content": chat.answer})

    return messages


@router.post(
    "/query",
    response_model=ChatQueryResponse,
    status_code=status.HTTP_200_OK
)
def query_repository(
    data: ChatQueryRequest,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(verify_token)
):
    """Answers developer queries and saves messages under the active session."""
    ai_service = AIService()
    response_payload = ai_service.generate_chat_response(
        project_id=data.project_id,
        question=data.question
    )

    # Persist question and answer under the specific session_id
    try:
        chat_entry = ChatHistory(
            project_id=data.project_id,
            session_id=data.session_id, # <-- Using active session target
            question=data.question,
            answer=response_payload["answer"]
        )
        db.add(chat_entry)
        db.commit()
    except Exception as db_err:
        print(f"⚠️ Failed to save session chat history: {str(db_err)}")
        db.rollback()

    return response_payload