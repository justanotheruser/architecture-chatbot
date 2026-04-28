import numpy as np
import faiss
from chatbot.ports import Index, Encoder


class FaissIndex(Index):
    def __init__(self, encoder: Encoder):
        super().__init__(encoder)
        self.index = faiss.IndexFlatL2(encoder.get_embedding_dimension())

    def add(self, texts: list[str]):
        embeddings = self.encoder.encode(texts)
        self.index.add(embeddings)  # type: ignore[call-args]

    def search(self, query: str, k: int) -> list[int]:
        query_embedding = self.encoder.encode([query])
        distances, indices = self.index.search(query_embedding, k)  # type: ignore[call-args]
        return indices[0]
