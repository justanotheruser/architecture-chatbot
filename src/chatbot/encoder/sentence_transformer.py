from chatbot.ports import Encoder
from sentence_transformers import SentenceTransformer
import numpy as np


class SentenceTransformerEncoder(Encoder):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.ascontiguousarray(self.model.encode(texts))

    def get_embedding_dimension(self) -> int:
        return self.model.get_embedding_dimension()  # type: ignore[call-arg]
