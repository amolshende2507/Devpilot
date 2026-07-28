from google import genai
from google.genai import types
from fastapi import HTTPException, status
from app.core.config import settings
from app.services.retrieval_service import RetrievalService


class AIService:
    SYSTEM_INSTRUCTIONS = (
        "You are DevPilot AI, an elite software architecture and code intelligence assistant.\n"
        "Your task is to answer user queries using ONLY the provided repository Code Context Blocks.\n\n"
        "Strict Guidelines:\n"
        "1. Base your answer solely on the provided code blocks.\n"
        "2. Do not write or reference functions, APIs, or classes that do not exist in the context.\n"
        "3. If the context does not contain enough information to answer the question, state: "
        "'I cannot find the answer in the provided repository context.' and do not make up hypothetical code.\n"
        "4. Always output your answer in clean Markdown. For code blocks, include the specific language, file name, and line numbers.\n"
    )

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY configuration is missing.")
        
        # New SDK Client Initialization
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.retrieval_service = RetrievalService()
        # Using the stable, high-limit production model
        self.model_name = "gemini-3.5-flash"

    def generate_chat_response(self, project_id: str, question: str) -> dict:
        """Orchestrates RAG: Retrieve context, build prompt, execute LLM call, return grounded answer."""
        try:
            chunks = self.retrieval_service.retrieve_relevant_context(
                project_id=project_id,
                query=question,
                limit=5
            )
        except Exception as ret_err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Context retrieval pipeline failed: {str(ret_err)}"
            )

        context_block = self.retrieval_service.build_llm_context_block(chunks)

        user_prompt = (
            f"User Question:\n{question}\n\n"
            f"Repository Code Context:\n"
            f"{context_block}\n\n"
            f"Answer:"
        )

        try:
            # New SDK execution structure
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.SYSTEM_INSTRUCTIONS,
                    temperature=0.1
                )
            )
        except Exception as ai_err:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Google LLM connection failed: {str(ai_err)}"
            )

        return {
            "answer": response.text if response.text else "Unable to generate a text response.",
            "retrieved_sources": chunks
        }