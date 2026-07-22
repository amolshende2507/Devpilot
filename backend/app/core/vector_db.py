import os
import chromadb
from chromadb.api import ClientAPI

# Initialize a persistent local disk client
# This saves our vector indices safely across server restarts
_chroma_client: ClientAPI | None = None


def get_chroma_client() -> ClientAPI:
    """Singleton getter for the persistent ChromaDB client."""
    global _chroma_client
    if _chroma_client is None:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.chroma"))
        print(f"⏳ Connecting to persistent ChromaDB at: {db_path}")
        _chroma_client = chromadb.PersistentClient(path=db_path)
        print("✅ Connected to ChromaDB.")
    return _chroma_client


def get_collection(name: str = "code_chunks"):
    """Fetches or creates a target semantic search vector collection."""
    client = get_chroma_client()
    # Return collection ready for writes or queries
    return client.get_or_create_collection(name=name)