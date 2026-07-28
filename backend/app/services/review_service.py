import os
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.project import Project
from app.models.repository_file import RepositoryFile


class ReviewService:
    REVIEW_SYSTEM_INSTRUCTIONS = (
        "You are an elite Staff Software Security Engineer and Principal Code Auditor.\n"
        "Your task is to analyze files from a user's repository and produce a rigorous, professional Code Review Report.\n\n"
        "Your report must be structured strictly in Markdown using these sections:\n"
        "1. 🚨 CRITICAL BUGS & LOGICAL FAILURES\n"
        "2. 🔒 SECURITY VULNERABILITIES (SQL Injection, Secret leaks, weak encryption, CORS)\n"
        "3. ⚡ PERFORMANCE BOTTLENECKS (N+1 queries, deadlocks, infinite loops, high memory operations)\n"
        "4. 💡 CLEAN CODE & REFACTORING SUGGESTIONS (Design patterns, modularity, legibility)\n\n"
        "Be extremely direct, technical, and precise. Quote specific file names and line boundaries when referencing issues, and provide copy-pasteable refactored code blocks."
    )

    def __init__(self, db: Session):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY configuration is missing.")
        
        # New SDK Client
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.db = db
        self.model_name = "gemini-3.5-flash"

    def review_project_codebase(self, project_id: str) -> dict:
        """Audits the files stored in a project database and compiles a code review report."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target project not found."
            )

        files = (
            self.db.query(RepositoryFile)
            .filter(RepositoryFile.project_id == project_id)
            .filter(RepositoryFile.language.in_(["py", "ts", "js", "go", "rs", "java", "sql"]))
            .limit(15)
            .all()
        )

        if not files:
            return {
                "project_id": project_id,
                "status": "skipped",
                "review_report": "No critical code files (Python, Go, JS, TS, Rust) were detected for audit."
            }

        code_payload = []
        for file in files:
            block = (
                f"--- Start of File: {file.path} ---\n"
                f"Language: {file.language}\n"
                f"{file.content}\n"
                f"--- End of File: {file.path} ---\n"
            )
            code_payload.append(block)

        concatenated_code = "\n\n".join(code_payload)

        prompt = (
            f"Analyze this repository codebase and compile a comprehensive Code Review Report:\n\n"
            f"{concatenated_code}\n\n"
            f"Detailed Report:"
        )

        try:
            # New SDK execution structure
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.REVIEW_SYSTEM_INSTRUCTIONS,
                    temperature=0.2
                )
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Automated Code Review execution failed: {str(e)}"
            )

        return {
            "project_id": project_id,
            "status": "completed",
            "review_report": response.text if response.text else "Unable to compile review metrics."
        }

    def generate_project_documentation(self, project_id: str) -> dict:
        """Analyzes folder structures and configuration files to write custom docs."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target project not found."
            )

        all_files = (
            self.db.query(RepositoryFile)
            .filter(RepositoryFile.project_id == project_id)
            .all()
        )

        if not all_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No files found in the database for this project."
            )

        file_paths = [file.path for file in all_files]
        directory_tree = "\n".join(f"- {path}" for path in sorted(file_paths))

        config_files = []
        target_configs = {
            "main.py", "requirements.txt", "package.json", 
            "docker-compose.yml", "Makefile", "go.mod", "cargo.toml"
        }

        for file in all_files:
            file_name = os.path.basename(file.path).lower()
            if file_name in target_configs:
                block = (
                    f"--- Configuration File: {file.path} ---\n"
                    f"{file.content}\n"
                )
                config_files.append(block)

        config_payload = "\n\n".join(config_files)

        doc_instructions = (
            "You are a Senior Technical Writer and Principal Systems Architect.\n"
            "Your task is to generate a comprehensive, highly professional README.md for the provided repository.\n\n"
            "The README must include these sections:\n"
            "1. 🚀 PROJECT INTRODUCTION (A clear description of what the project does based on its codebase)\n"
            "2. 📦 TECH STACK & DEPENDENCIES (Identified from the configuration files provided)\n"
            "3. 📂 SYSTEM ARCHITECTURE & FILE TREE (Explain the directory structure and the role of key folders)\n"
            "4. ⚙️ LOCAL BOOTSTRAPPING GUIDE (Provide step-by-step terminal commands to set up, install, configure, and launch the project)\n\n"
            "Use clean, professional Markdown formatting."
        )

        prompt = (
            f"Generate a production-ready README.md using this repository context:\n\n"
            f"=== PROJECT DIRECTORY FILE TREE ===\n"
            f"{directory_tree}\n\n"
            f"=== CORE CONFIGURATION FILES ===\n"
            f"{config_payload}\n\n"
            f"Generated README.md Content:"
        )

        try:
            # New SDK execution structure
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=doc_instructions,
                    temperature=0.2
                )
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Documentation generation failed: {str(e)}"
            )

        return {
            "project_id": project_id,
            "status": "completed",
            "readme_content": response.text if response.text else "Unable to compile documentation."
        }