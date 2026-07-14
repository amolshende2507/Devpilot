import os
import shutil
import tempfile
import stat  # <-- NEW: Used for manipulating Windows file flags
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from git import Repo
from app.models.project import Project
from app.models.repository_file import RepositoryFile


def remove_readonly(func, path, excinfo):
    """Helper function to clear Windows read-only file permissions and retry deletion."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


class RepositoryService:
    # Set of file extensions we want to index
    SUPPORTED_EXTENSIONS = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".go", 
        ".rs", ".java", ".cpp", ".c", ".h", ".cs", 
        ".md", ".json", ".yaml", ".yml", ".sql", ".html", ".css"
    }

    # Directories we absolutely want to skip
    IGNORED_DIRECTORIES = {
        ".git", "node_modules", "venv", "env", ".venv", 
        "__pycache__", "dist", "build", "target", "out",
        ".next", ".idea", ".vscode"
    }

    def __init__(self, db: Session):
        self.db = db

    def import_repository(self, user_id: str, name: str, github_url: str) -> Project:
        """Initializes a new project tracking record in the local database."""
        project = Project(
            user_id=user_id,
            name=name,
            github_url=github_url,
            status="pending"
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def process_repository(self, project_id: str) -> dict:
        """Clones, filters, and extracts text content of repository files."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("Target project does not exist.")

        # Update status to show we are actively processing
        project.status = "cloning"
        self.db.commit()

        # Create a secure temporary directory on the host disk
        temp_dir = tempfile.mkdtemp()
        print(f"⏳ Local workspace initialized at: {temp_dir}")

        try:
            # 1. Clone the public repository
            print(f"⏳ Cloning {project.github_url}...")
            Repo.clone_from(project.github_url, temp_dir, depth=1)
            
            project.status = "indexing"
            self.db.commit()
            print("✅ Cloning complete. Starting directory scan...")

            # 2. Walk the workspace and process files
            saved_count = 0
            for root, dirs, files in os.walk(temp_dir):
                dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRECTORIES]

                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in self.SUPPORTED_EXTENSIONS:
                        full_path = os.path.join(root, file)
                        relative_path = os.path.relpath(full_path, temp_dir)
                        
                        try:
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                file_content = f.read()

                            if file_content.strip():
                                repo_file = RepositoryFile(
                                    project_id=project.id,
                                    path=relative_path,
                                    language=ext.strip("."),
                                    content=file_content
                                )
                                self.db.add(repo_file)
                                saved_count += 1
                        except Exception as file_err:
                            print(f"⚠️ Skipped processing file {relative_path}: {str(file_err)}")

            self.db.commit()
            project.status = "completed"
            self.db.commit()
            print(f"✅ Processing complete! Indexed {saved_count} files.")
            return {"status": "success", "files_indexed": saved_count}

        except Exception as e:
            self.db.rollback()
            project.status = "failed"
            self.db.commit()
            print(f"❌ Failed to process repository {project.github_url}: {str(e)}")
            return {"status": "failed", "error": str(e)}

        finally:
            # Cleanup Disk: Handle Windows file locking cleanly
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, onerror=remove_readonly) # <-- NEW: Pass our handler
                print(f"Temporary workspace {temp_dir} cleaned from disk.")