import time
from typing import List
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    # Class-level static variable to hold our shared model instance (Singleton)
    _model_instance: SentenceTransformer | None = None

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name

    @classmethod
    def get_model(cls, model_name: str) -> SentenceTransformer:
        """Thread-safe lazy initializer. Loads the model into RAM only on first call."""
        if cls._model_instance is None:
            print(f"⏳ Loading Local Embedding Model '{model_name}' into RAM (First-time load)...")
            start_time = time.time()
            # Loads the PyTorch weights on CPU (or GPU if CUDA is configured)
            cls._model_instance = SentenceTransformer(model_name)
            elapsed_time = time.time() - start_time
            print(f"✅ Model successfully loaded in {elapsed_time:.2f} seconds.")
        return cls._model_instance

    def generate_embedding(self, text: str) -> List[float]:
        """Generates a dense vector embedding array for a single text chunk."""
        model = self.get_model(self.model_name)
        # Convert Python string into a dense float vector
        vector = model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of text chunks in parallel.
        
        Batch processing is significantly faster than processing files individually 
        because it allows the neural network to execute matrix operations in parallel.
        """
        if not texts:
            return []
        
        model = self.get_model(self.model_name)
        # Execute batch inference
        vectors = model.encode(texts, batch_size=32, show_progress_bar=False, convert_to_numpy=True)
        return vectors.tolist()