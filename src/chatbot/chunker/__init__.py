from pathlib import Path
from chatbot.models import DataChunk
import sqlite3
from abc import ABC, abstractmethod
from chatbot.config import ChunkerConfig


class Chunker(ABC):
    """Читает документы и разбивает их на куски; умеет сохранять результат в SQLite и загружать из него"""

    def __init__(self, config: ChunkerConfig) -> None:
        self.cfg = config
        self.chunks: list[DataChunk] = []

    @abstractmethod
    def chunk_folder(self, path: Path) -> None: ...

    @abstractmethod
    def chunk_file(self, path: Path) -> None: ...

    def save_to_sqlite(self, db_path: Path) -> None:
        if db_path.exists():
            db_path.unlink()
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY AUTOINCREMENT, page_title TEXT, sections TEXT, text TEXT)"
            )
            conn.executemany(
                "INSERT INTO chunks (page_title, sections, text) VALUES (?, ?, ?)",
                [
                    (chunk.page_title, chunk.sections, chunk.text)
                    for chunk in self.chunks
                ],
            )

    @staticmethod
    def load_from_sqlite(db_path: Path) -> list[DataChunk]:
        chunks: list[DataChunk] = []
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chunks")
            for row in cursor.fetchall():
                chunks.append(DataChunk(row[1], row[2], row[3]))
        return chunks
