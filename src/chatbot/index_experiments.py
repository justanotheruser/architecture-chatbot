from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

sentences = [
    "Hello, world!", 
    "Mitochondria is the powerhouse of the cell.", 
    "London is the capital of Great Britain.",
]

model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

def encode_sentences(sentences: list[str]) -> np.ndarray:
    encoded = model.encode(sentences)
    return np.ascontiguousarray(encoded)


def build_index(encoded: np.ndarray) -> faiss.Index:
    index = faiss.IndexFlatL2(encoded.shape[1])
    index.add(encoded)  # type: ignore[call-args]
    return index

encoded = encode_sentences(sentences)
index = build_index(encoded)

query = ["Paris is the capital of France.", "Goodbye, world!"]
query_encoded = encode_sentences(query)
V, I = index.search(query_encoded, 2)  # type: ignore[call-args]
print(I)
print(V)