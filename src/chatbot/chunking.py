import pathlib
import re
from collections import deque

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
    # Отслеживает текущую наду для каждого уровня заголовков
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


if __name__ == "__main__":  
    wiki_path = pathlib.Path(__file__).parent.parent.parent / "wiki" / "wiki"
    for file in wiki_path.glob("*.md"):
        text = file.read_text(encoding="utf-8")
        chunks = chunk_markdown(text, chunk_size=1000, overlap_ratio=0.2)
        print(file.name)
        for title, chunk in chunks.items():
            print(f"{title}: {len(chunk)} lines")
            print()