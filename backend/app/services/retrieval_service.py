from typing import List, Dict, Any
from app.services.embedding_service import EmbeddingService
from app.core.vector_db import get_collection


class RetrievalService:
    def __init__(self, collection_name: str = "code_chunks"):
        self.embedding_service = EmbeddingService()
        self.collection = get_collection(collection_name)

    def retrieve_relevant_context(self, project_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves the top-K most semantically relevant code chunks for a query.
        
        Enforces strict project segmentation using metadata filters.
        """
        # 1. Convert the user's question into a query vector using our local model
        query_vector = self.embedding_service.generate_embedding(query)

        # 2. Query ChromaDB using strict project isolation
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=limit,
            where={"project_id": project_id}  # Enforces project boundaries
        )

        formatted_results: List[Dict[str, Any]] = []
        
        # Check if we got results
        if not results or not results.get("documents") or len(results["documents"][0]) == 0:
            return formatted_results

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(documents)

        # 3. Restructure raw vector payloads into a clean schema
        for idx in range(len(documents)):
            formatted_results.append({
                "content": documents[idx],          # The code snippet containing our structural headers
                "metadata": metadatas[idx],          # File path, start line, end line, language
                "relevance_distance": distances[idx] # Cosine distance score
            })

        return formatted_results

    def build_llm_context_block(self, chunks: List[Dict[str, Any]]) -> str:
        """Assembles multiple retrieved code chunks into a single formatted markdown context block."""
        if not chunks:
            return "No matching code context was found in the repository index."

        context_blocks = []
        for idx, chunk in enumerate(chunks, 1):
            meta = chunk["metadata"]
            block = (
                f"### Code Context Block {idx} (File: {meta.get('file_path')} | Lines: {meta.get('start_line')}-{meta.get('end_line')})\n"
                "```" + f"{meta.get('language', '')}\n"
                f"{chunk['content']}\n"
                "```\n"
            )
            context_blocks.append(block)

        return "\n".join(context_blocks)