from chatbot.chunker import Chunker
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from chatbot.models import DataChunk
import orjson

DROP_SELECTORS = [
    "script",
    "style",    
    "noscript",
    ".mw-editsection",
    ".reference",
    ".references",
    ".navbox",
    ".metadata",
    ".toc",
]




class WikiJsonChunker(Chunker):
    def chunk_folder(self, path: Path) -> None:
        for file in path.rglob("*.json"):
            print(file)
            self.chunk_file(file)

    def chunk_file(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        page_data = orjson.loads(text)
        title = page_data["title"]
        for section in clean_html_to_sections(page_data["html"]):
            self.chunks.append(DataChunk(title, ' > '.join(section["section_path"]), section["text"]))


def clean_html_to_sections(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    for selector in DROP_SELECTORS:
        for node in soup.select(selector):
            node.decompose()

    sections = []
    current_path = []
    current_blocks = []

    def flush():
        nonlocal current_blocks
        text = "\n".join(block for block in current_blocks if block.strip()).strip()
        if text:
            sections.append({
                "section_path": current_path.copy(),
                "text": text,
            })
        current_blocks = []

    for node in soup.find_all(["h2", "h3", "h4", "p", "li"]):
        if not isinstance(node, Tag):
            continue

        if node.name in ["h2", "h3", "h4"]:
            flush()
            level = int(node.name[1])
            title = node.get_text(" ", strip=True)

            if not title:
                continue

            # h2 -> уровень 0, h3 -> уровень 1, h4 -> уровень 2
            depth = level - 2
            current_path = current_path[:depth]
            current_path.append(title)

        elif node.name in ["p", "li"]:
            text = node.get_text(" ", strip=True)
            if text:
                current_blocks.append(text)

    flush()
    return sections