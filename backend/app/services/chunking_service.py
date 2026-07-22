import os
from typing import List
from app.models.repository_file import RepositoryFile
from app.schemas.chunk import CodeChunk


class ChunkingService:
    # Heuristics keywords that signify the start of a logical code construct
    LOGICAL_BOUNDARIES = {
        "class ", "def ", "function ", "async def ", 
        "const ", "let ", "var ", "export ", "interface ", "struct "
    }

    def __init__(self, max_lines: int = 40, overlap_lines: int = 5):
        """Initializes chunk boundaries.
        
        Args:
            max_lines: The maximum line height of an individual chunk.
            overlap_lines: Number of lines duplicated across adjacent chunks to preserve flow.
        """
        self.max_lines = max_lines
        self.overlap_lines = overlap_lines

    def split_file(self, file: RepositoryFile) -> List[CodeChunk]:
        """Splits a single file into logical, overlapping code chunks."""
        lines = file.content.splitlines()
        total_lines = len(lines)
        chunks: List[CodeChunk] = []

        if total_lines == 0:
            return chunks

        # If the file is extremely short, return it as a single chunk
        if total_lines <= self.max_lines:
            content = self._format_chunk_content(file.path, file.language, 1, total_lines, file.content)
            chunks.append(
                CodeChunk(
                    project_id=file.project_id,
                    file_path=file.path,
                    language=file.language if file.language else "text",
                    start_line=1,
                    end_line=total_lines,
                    content=content,
                    raw_code=file.content
                )
            )
            return chunks

        start_idx = 0
        while start_idx < total_lines:
            # Determine end boundary for this chunk
            end_idx = min(start_idx + self.max_lines, total_lines)

            # Heuristic Optimization: 
            # If we are not at the end of the file, try to shift our boundary slightly backward
            # to break at a natural logical boundary (like a new class or function definition)
            if end_idx < total_lines:
                adjusted_boundary = False
                # Look back up to 'overlap_lines' lines to find a clean break point
                for lookback in range(1, self.overlap_lines + 1):
                    target_idx = end_idx - lookback
                    if target_idx <= start_idx:
                        break
                    
                    line_content = lines[target_idx].strip()
                    if any(line_content.startswith(bound) for bound in self.LOGICAL_BOUNDARIES):
                        end_idx = target_idx  # Adjust boundary to start right before this keyword
                        adjusted_boundary = True
                        break

            # Extract chunk lines
            chunk_lines = lines[start_idx:end_idx]
            raw_chunk_text = "\n".join(chunk_lines)
            
            # Format raw chunk with rich context headers (critical for LLM RAG injection)
            formatted_content = self._format_chunk_content(
                file_path=file.path,
                language=file.language if file.language else "text",
                start_line=start_idx + 1,
                end_line=end_idx,
                code=raw_chunk_text
            )

            chunks.append(
                CodeChunk(
                    project_id=file.project_id,
                    file_path=file.path,
                    language=file.language if file.language else "text",
                    start_line=start_idx + 1,
                    end_line=end_idx,
                    content=formatted_content,
                    raw_code=raw_chunk_text
                )
            )

            # Advance the sliding window, preserving the configured overlap
            start_idx = end_idx - self.overlap_lines
            if start_idx >= end_idx:  # Prevent infinite loops in edge-case files
                start_idx = end_idx

        return chunks

    def _format_chunk_content(self, file_path: str, language: str, start_line: int, end_line: int, code: str) -> str:
        """Injects clean context headers directly into the text chunk.
        
        This guarantees that when the vector database retrieves the chunk,
        the LLM reads the exact directory structure and boundaries of the snippet.
        """
        return (
            f"// File: {file_path}\n"
            f"// Language: {language}\n"
            f"// Lines: {start_line}-{end_line}\n"
            "// ==========================================\n"
            f"{code}"
        )