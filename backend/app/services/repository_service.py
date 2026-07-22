import os
import shutil
import tempfile
import stat
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from git import Repo

from app.models.project import Project
from app.models.repository_file import RepositoryFile

# Import our code-intelligence dependencies
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.core.vector_db import get_collection


def remove_readonly(func, path, excinfo):
    """Helper function to clear Windows read-only file permissions and retry deletion."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


class RepositoryService:
    SUPPORTED_EXTENSIONS = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".go", 
        ".rs", ".java", ".cpp", ".c", ".h", ".cs", 
        ".md", ".json", ".yaml", ".yml", ".sql", ".html", ".css"
    }

    IGNORED_DIRECTORIES = {
        ".git", "node_modules", "venv", "env", ".venv", 
        "__pycache__", "dist", "build", "target", "out",
        ".next", ".idea", ".vscode"
    }

    def __init__(self, db: Session):
        self.db = db
        # Initialize our local NLP dependencies
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()

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
        """Clones, indexes, and generates vector embeddings for repository files."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("Target project does not exist.")

        project.status = "cloning"
        self.db.commit()

        temp_dir = tempfile.mkdtemp()
        print(f"⏳ Local workspace initialized at: {temp_dir}")

        try:
            # 1. Clone the repository
            print(f"⏳ Cloning {project.github_url}...")
            Repo.clone_from(project.github_url, temp_dir, depth=1)
            
            project.status = "indexing"
            self.db.commit()
            print("✅ Cloning complete. Starting directory scan...")

            # 2. Walk and extract files
            saved_files: list[RepositoryFile] = []
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
                                saved_files.append(repo_file)
                        except Exception as file_err:
                            print(f"⚠️ Skipped processing file {relative_path}: {str(file_err)}")

            # Save raw file payloads in PostgreSQL
            self.db.commit()
            print(f"✅ Saved {len(saved_files)} files in PostgreSQL. Running Vectorization...")

            # 3. Vectorization & Seeding Pipeline
            collection = get_collection() # Retrieve our ChromaDB index
            total_chunks_indexed = 0

            for file in saved_files:
                # A. Generate smart structural text chunks
                chunks = self.chunking_service.split_file(file)
                if not chunks:
                    continue

                # Prepare batches for ChromaDB
                chunk_ids: list[str] = []
                chunk_texts: list[str] = []
                chunk_metadatas: list[dict] = []

                for chunk in chunks:
                    # Generate a unique key for each chunk
                    chunk_id = f"chunk_{uuid.uuid4()}"
                    chunk_ids.append(chunk_id)
                    chunk_texts.append(chunk.content) # Injected with rich directory headers
                    
                    # Store precise relational file properties as vector metadata
                    chunk_metadatas.append({
                        "project_id": project.id,
                        "file_path": file.path,
                        "language": file.language if file.language else "text",
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line
                    })

                # B. Batch-generate local embedding vectors
                # This is highly optimized (matrix-matrix parallel math)
                chunk_embeddings = self.embedding_service.generate_embeddings(chunk_texts)

                # C. Write directly to ChromaDB
                collection.add(
                    ids=chunk_ids,
                    embeddings=chunk_embeddings,
                    documents=chunk_texts,
                    metadatas=chunk_metadatas
                )
                total_chunks_indexed += len(chunks)

            project.status = "completed"
            self.db.commit()
            print(f"🎉 Ingestion pipeline complete! Indexed {len(saved_files)} files into {total_chunks_indexed} vector chunks.")
            return {"status": "success", "files_indexed": len(saved_files), "vector_chunks": total_chunks_indexed}

        except Exception as e:
            self.db.rollback()
            project.status = "failed"
            self.db.commit()
            
            # NEW: Import traceback and print the complete active stack trace to terminal
            import traceback
            print("\n❌ CRITICAL EXCEPTION IN PROCESS_REPOSITORY:")
            traceback.print_exc() 
            print("\n")
            
            return {"status": "failed", "error": str(e)}

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, onerror=remove_readonly)
                print(f"🧹 Temporary workspace {temp_dir} cleaned from disk.")