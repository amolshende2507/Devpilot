import google.generativeai as genai
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
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.db = db
        self.model = genai.GenerativeModel(
            model_name="gemini-3.5-flash",
            system_instruction=self.REVIEW_SYSTEM_INSTRUCTIONS
        )

    def review_project_codebase(self, project_id: str) -> dict:
        """Audits the files stored in a project database and compiles a code review report."""
        
        # 1. Fetch the project and its files
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target project not found."
            )

        # Retrieve files (limit to top 15 critical code files to fit context budgets safely)
        # We prioritize backend files over frontend/config assets
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

        # 2. Assemble the Codebase Payload
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

        # 3. Construct prompt
        prompt = (
            f"Analyze this repository codebase and compile a comprehensive Code Review Report:\n\n"
            f"{concatenated_code}\n\n"
            f"Detailed Report:"
        )

        # 4. Generate report
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.2} # Low temperature ensures analytical precision
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