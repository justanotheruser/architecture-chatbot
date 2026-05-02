import faiss
from chatbot.ports import Index, Encoder
from chatbot.config import IndexConfig
from pathlib import Path


class FaissIndex(Index):
    def __init__(self, encoder: Encoder, cfg: IndexConfig):
        super().__init__(encoder)
        self.cfg = cfg
        self.index = faiss.IndexFlatL2(encoder.get_embedding_dimension())

    def read_index(self, index_file_name: Path) -> bool:
        if not index_file_name.exists():
            return False
        self.index = faiss.read_index(str(index_file_name))
        return True

    def add(self, texts: list[str]):
        embeddings = self.encoder.encode(texts)
        self.index.add(embeddings)  # type: ignore[call-args]

    def search(self, query: str, k: int) -> list[int]:
        query_embedding = self.encoder.encode([query])
        distances, indices = self.index.search(query_embedding, k)  # type: ignore[call-args]
        return indices[0]

    def write_index(self, index_file_name: Path) -> None:
        faiss.write_index(self.index, str(index_file_name))