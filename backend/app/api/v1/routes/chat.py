from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.ai_service import AIService
from app.core.security import verify_token
from app.models.chat import ChatHistory # <-- NEW

router = APIRouter(
    prefix="/chat",
    tags=["AI Code Chat"]
)


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
    """Answers developer queries and saves the conversation in database history."""
    ai_service = AIService()
    response_payload = ai_service.generate_chat_response(
        project_id=data.project_id,
        question=data.question
    )

    # NEW: Persist the question and answer to our PostgreSQL database
    try:
        chat_entry = ChatHistory(
            project_id=data.project_id,
            question=data.question,
            answer=response_payload["answer"]
        )
        db.add(chat_entry)
        db.commit()
    except Exception as db_err:
        print(f"⚠️ Failed to save chat history: {str(db_err)}")
        # We do not block the user's response if the history write fails
        db.rollback()

    return response_payload


@router.get(
    "/project/{project_id}",
    status_code=status.HTTP_200_OK
)
def get_project_chat_history(
    project_id: str,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(verify_token)
):
    """Fetches the past chat conversations for a target repository project."""
    # Ensure user has access
    user_id = user_payload.get("sub")
    if not user_id:
         raise HTTPException(status_code=401, detail="Unauthorized")

    # Retrieve entries sorted chronologically
    chats = (
        db.query(ChatHistory)
        .filter(ChatHistory.project_id == project_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )

    # Format into a clean message list for our React state
    messages = []
    for chat in chats:
        messages.append({"role": "user", "content": chat.question})
        messages.append({"role": "assistant", "content": chat.answer})

    return messages