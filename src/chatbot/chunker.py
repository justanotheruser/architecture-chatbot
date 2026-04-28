from pathlib import Path
import re
from collections import deque
import sqlite3
from chatbot.models import DataChunk
from pydantic import BaseModel


class ChunkerConfig(BaseModel):
    chunk_size: int
    overlap_ratio: float


class Chunker:
    """Читает документы и разбивает их на куски; умеет сохранять результат в SQLite и загружать из него"""
    def __init__(self, config: ChunkerConfig) -> None:
        self.cfg = config
        self.chunks: list[DataChunk] = []

    def chunk_markdown_folder(self, path: Path) -> None:
        for file in path.rglob("*.md"):
            print(file)
            self.chunk_markdown_file(file)

    def chunk_markdown_file(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        chunks = chunk_markdown(text, chunk_size=self.cfg.chunk_size, overlap_ratio=self.cfg.overlap_ratio)
        for title, chunk in chunks.items():
            print(f"{title}: {len(chunk)} lines")
        self.chunks.extend([DataChunk(path.name, title, chunk) for title, chunk in chunks.items()])

    def save_to_sqlite(self, db_path: Path) -> None:
        if db_path.exists():
            db_path.unlink()
        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY AUTOINCREMENT, file_name TEXT, title TEXT, text TEXT)")
            conn.executemany("INSERT INTO chunks (file_name, title, text) VALUES (?, ?, ?)", [(chunk.file_name, chunk.title, chunk.text) for chunk in self.chunks])

    @staticmethod
    def load_from_sqlite(db_path: Path) -> list[DataChunk]:
        chunks: list[DataChunk] = []
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chunks")
            for row in cursor.fetchall():
                chunks.append(DataChunk(row[1], row[2], row[3]))
        return chunks


class MarkDownNode:
    def __init__(self, title: str) -> None:
        self.title = title
        self.content: list[str] = []
        self.children: list[MarkDownNode] = []


def split_markdown_sections(text: str, max_title_level: int = 2, title_delimiter: str = " / ") -> dict[str, str]:
    root = build_markdown_tree(text, max_title_level)
    sections: dict[str, str] = {}

    def add_section(title: str, content: list[str]) -> None:
        content_text = "\n".join(content).strip()
        if content_text:
            sections[title] = content_text

    def flatten_tree(node: MarkDownNode, prefix: str, sections: dict[str, str]) -> None:
        add_section(f"{prefix}{node.title}", node.content)
        for child in node.children:
            flatten_tree(child, f"{prefix}{node.title}{title_delimiter}", sections)

    # Избегаем лишнего разделителя в начале всех заголовков
    add_section("", root.content)
    for child in root.children:
        flatten_tree(child, "", sections)
    return sections


def build_markdown_tree(text: str, max_title_level: int) -> MarkDownNode:
    header_pattern = r"(?P<level>#+)\s*(?P<title>.*)"
    # Отслеживает текущую ноду для каждого уровня заголовков
    # Например, nodes[0] - это корневой узел, nodes[1] - текущий '# Заголовок 1', nodes[2] - текущий '## Подзаголовок 1.4', и т.д.
    root = MarkDownNode("")
    nodes: deque[MarkDownNode] = deque([root])

    for line in text.split("\n"):
        if match := re.match(header_pattern, line):
            new_header_level = len(match.group("level"))
            if new_header_level > max_title_level:
                # если новый уровень заголовка больше максимального уровня, то не создаём новый узел
                nodes[-1].content.append(line)
                continue
            # Текущий раздел закончился, начался новый
            while new_header_level < len(nodes):
                nodes.pop()
            new_node = MarkDownNode(match.group("title"))
            nodes[-1].children.append(new_node)
            nodes.append(new_node)
        else:
            # если это не заголовок, то добавляем в текущий узел
            nodes[-1].content.append(line)
    
    return root

def chunk_markdown(text: str, chunk_size: int, overlap_ratio: float) -> dict[str, str]:
    assert 0 <= overlap_ratio < 1
    overlap_size = int(chunk_size * overlap_ratio)
    sections = split_markdown_sections(text)
    chunks = {}
    for title, section in sections.items():
        if len(section) <= chunk_size:
            chunks[title] = section
            continue
        start = 0
        end = chunk_size
        i = 1
        while end < len(section):
            chunk_title = f"{title} [part {i}]"
            chunks[chunk_title] = section[start:end]
            start = end - overlap_size
            end = start + chunk_size
            i += 1
        end = len(section)
        if section[start:end]:
            chunk_title = f"{title} [part {i}]"
            chunks[chunk_title] = section[start:end]
    return chunks