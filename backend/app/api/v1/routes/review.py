from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.review import ProjectReviewResponse, ProjectDocsResponse
from app.services.review_service import ReviewService
from app.core.security import verify_token

router = APIRouter(
    prefix="/review",
    tags=["Automated Code Review"]
)


@router.post(
    "/project/{project_id}",
    response_model=ProjectReviewResponse,
    status_code=status.HTTP_200_OK
)
def run_codebase_review(
    project_id: str,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(verify_token)
):
    """Executes a semantic code review across files in the target project."""
    review_service = ReviewService(db)
    response_payload = review_service.review_project_codebase(project_id)
    return response_payload

@router.post(
    "/project/{project_id}/docs",
    response_model=ProjectDocsResponse,
    status_code=status.HTTP_200_OK
)
def run_codebase_documentation(
    project_id: str,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(verify_token)
):
    """Analyzes repository structures to autonomously generate a production README.md."""
    review_service = ReviewService(db)
    response_payload = review_service.generate_project_documentation(project_id)
    return response_payload