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

    # NEW: Highly focused prompt instructions for the Query Expander
    EXPANDER_INSTRUCTIONS = (
        "You are an elite search optimization engine.\n"
        "Your task is to translate lazy or short developer questions into a rich, highly descriptive list of technical keywords, "
        "function signatures, and database structures that would be found in source code files.\n"
        "Output ONLY the optimized technical search string. Do not include introductory text or formatting."
    )

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY configuration is missing.")
        
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.retrieval_service = RetrievalService()
        self.model_name = "gemini-3.5-flash"

    def expand_developer_query(self, raw_query: str) -> str:
        """Autonomously expands short or lazy queries into rich technical search strings."""
        # If the query is already long and detailed, we bypass expansion to save latency
        if len(raw_query.split()) > 10:
            return raw_query

        try:
            prompt = (
                f"Translate this simple query into a rich, technical source-code search query:\n"
                f"Query: '{raw_query}'\n"
                f"Optimized Search String:"
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.EXPANDER_INSTRUCTIONS,
                    temperature=0.1
                )
            )
            expanded = response.text.strip() if response.text else raw_query
            print(f"🤖 Query Expansion: '{raw_query}' ──> '{expanded}'")
            return expanded
        except Exception as e:
            # Fallback: If the expansion fails (e.g. rate limit), use the raw query
            print(f"⚠️ Query Expansion bypassed: {str(e)}")
            return raw_query

    def generate_chat_response(self, project_id: str, question: str) -> dict:
        """Orchestrates RAG: Expand, Retrieve, Build Prompt, Generate Answer."""
        
        # 1. NEW: Expand query to align prompt context semantics
        search_query = self.expand_developer_query(question)

        # 2. Retrieve relevant chunks using the expanded technical search string
        try:
            chunks = self.retrieval_service.retrieve_relevant_context(
                project_id=project_id,
                query=search_query, # <-- Pass the expanded search string
                limit=3
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