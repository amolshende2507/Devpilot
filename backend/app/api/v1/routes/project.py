from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue

from app.db.database import get_db
from app.schemas.project import ProjectImportRequest, ProjectResponse
from app.services.repository_service import RepositoryService
from app.core.security import verify_token
from app.core.config import settings
from app.models.project import Project # <-- NEW: Swapped import mapping
from app.core.vector_db import get_collection # <-- NEW
router = APIRouter(
    prefix="/projects",
    tags=["Projects & Repositories"]
)

# Initialize Redis connection client and target task queue
redis_conn = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
task_queue = Queue("ingestion_queue", connection=redis_conn)


@router.post(
    "/import",
    response_model=ProjectResponse,
    status_code=status.HTTP_202_ACCEPTED
)
def import_repo(
    data: ProjectImportRequest,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(verify_token)
):
    """Initializes a project tracking entity and enqueues the cloning task asynchronously."""
    user_id = user_payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identifier missing from credential context."
        )

    repo_service = RepositoryService(db)
    
    # Create the project entity in PostgreSQL (status initialized as 'pending')
    project = repo_service.import_repository(
        user_id=user_id,
        name=data.name,
        github_url=data.github_url
    )

    from app.tasks.ingestion import process_repository_task

    try:
        task_queue.enqueue(
            process_repository_task,
            project.id,
            job_id=f"ingest_{project.id}"
        )
    except Exception as redis_err:
        print(f"⚠️ Failed to queue background job: {str(redis_err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task broker is currently unreachable. Please retry in a moment."
        )

    return project


@router.get(
    "",
    response_model=list[ProjectResponse],
    status_code=status.HTTP_200_OK
)
def list_projects(
    db: Session = Depends(get_db),
    user_payload: dict = Depends(verify_token)
):
    """Fetches all repository project structures belonging to the authenticated user."""
    user_id = user_payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User identifier missing from credential context."
        )

    # Query public.projects where user_id matches
    projects = db.query(Project).filter(Project.user_id == user_id).all()
    return projects

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    user_payload: dict = Depends(verify_token)
):
    """Deletes a repository index, purges its vectors from ChromaDB, and cascade-deletes Postgres records."""
    user_id = user_payload.get("sub")
    
    # 1. Locate the project and verify ownership
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository index not found or unauthorized access."
        )

    # 2. Vector Cleanup: Delete all matching code vectors from ChromaDB
    try:
        collection = get_collection()
        # ChromaDB supports metadata filters during deletions
        collection.delete(where={"project_id": project_id})
        print(f"🧹 ChromaDB: Purged code vectors for Project ID: {project_id}")
    except Exception as e:
        print(f"⚠️ Failed to purge vectors from ChromaDB during project deletion: {str(e)}")
        # We do not block database deletions if Chroma is temporarily unreachable

    # 3. Relational Cleanup: Delete project from PostgreSQL
    # (Cascade-deletes files, chats, and sessions)
    db.delete(project)
    db.commit()
    
    return None