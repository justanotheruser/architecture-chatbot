from typing import Protocol
import numpy as np


class Encoder(Protocol):
    def get_embedding_dimension(self) -> int: ...

    def encode(self, texts: list[str]) -> np.ndarray: ...


class Index(Protocol):
    encoder: Encoder

    def __init__(self, encoder: Encoder):
        self.encoder = encoder

    def add(self, texts: list[str]) -> None: ...

    def search(self, query: str, k: int) -> list[int]: ...
