from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.project import ProjectImportRequest, ProjectResponse
from app.services.repository_service import RepositoryService
from app.core.security import verify_token

router = APIRouter(
    prefix="/projects",
    tags=["Projects & Repositories"]
)


@router.post(
    "/import",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
def import_repo(
    data: ProjectImportRequest,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(verify_token)
):
    """Initializes and clones a repository to extract contents."""
    user_id = user_payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identifier missing from credential context."
        )

    repo_service = RepositoryService(db)
    
    # 1. Create the project tracking entity in our DB
    project = repo_service.import_repository(
        user_id=user_id,
        name=data.name,
        github_url=data.github_url
    )

    # 2. Process the files (cloning, parsing, and storing)
    # Note: This is synchronous right now. We will test it synchronously to make sure
    # our logic is flawless before adding asynchronous background queue workers.
    result = repo_service.process_repository(project.id)
    
    if result.get("status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Repository analysis failed: {result.get('error')}"
        )

    # Re-query the updated project payload from DB
    db.refresh(project)
    return project