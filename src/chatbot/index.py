from typing import Protocol
import numpy as np
from chatbot.models import DataChunk


class Index(Protocol):
    def search(self, query_embedding: np.ndarray, k: int) -> list[DataChunk]:
        ...



import faiss
    
class FaissIndex(Index):
    def __init__(self, embeddings: np.ndarray, chunks: list[DataChunk]):
        assert embeddings.shape[0] == len(chunks), "Number of embeddings and chunks must be the same"
        self.embeddings = embeddings
        self.chunks = chunks
        self.index = faiss.IndexFlatL2(embeddings.shape[1])

    def search(self, query_embedding: np.ndarray, k: int) -> list[DataChunk]:
        distances, indices = self.index.search(query_embedding, k)  # type: ignore[call-args]
        return [self.chunks[i] for i in indices[0]]
