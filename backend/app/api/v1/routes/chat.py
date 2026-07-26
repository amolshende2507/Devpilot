from fastapi import APIRouter, Depends, status
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.ai_service import AIService
from app.core.security import verify_token

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
    user_payload: dict = Depends(verify_token)
):
    """Answers developer queries grounded in the context of the target repository."""
    ai_service = AIService()
    response_payload = ai_service.generate_chat_response(
        project_id=data.project_id,
        question=data.question
    )
    return response_payload