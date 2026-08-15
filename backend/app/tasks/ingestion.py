# --- CRITICAL FIX ---
# We import our base registry. This forces SQLAlchemy to load and map User, Project,
# and RepositoryFile, resolving foreign-key compilation errors in isolated background workers.
from app.db.base import Base  # noqa

from app.db.database import SessionLocal
from app.services.repository_service import RepositoryService


def process_repository_task(project_id: str):
    """Asynchronous background task executed by the RQ worker.
    
    This handles cloning, chunking, and embedding out-of-band.
    """
    print(f"🚀 RQ Worker: Starting background ingestion task for Project ID: {project_id}")
    
    # Establish an isolated database session for the worker process
    db = SessionLocal()
    try:
        service = RepositoryService(db)
        result = service.process_repository(project_id)
        print(f"✅ RQ Worker: Finished background ingestion. Result: {result}")
    except Exception as e:
        print(f"❌ RQ Worker: Critical background task crash: {str(e)}")
    finally:
        db.close()