from pydantic import BaseModel


class CodeChunk(BaseModel):
    project_id: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    content: str  # The raw code string including context headers
    raw_code: str # The clean code snippet without metadata headers