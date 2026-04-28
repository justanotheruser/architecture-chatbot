from chatbot.chunking import build_markdown_tree
from chatbot.chunking import MarkDownNode


def restore_markdown_from_tree(node: MarkDownNode, level: int = 0) -> str:
    text = ""
    if node.title:
        text += f"{'#' * level} {node.title}\n"
    if node.content:
        text += "\n".join(node.content)
    children_text = "\n".join(
        [restore_markdown_from_tree(child, level + 1) for child in node.children]
    )
    if children_text:
        text += "\n" + children_text
    return text


def test_build_markdown_tre_simple():
    text = """
# Заголовок 1
Здесь текст для заголовка 1
## Заголовок 1.1
Здесь текст для заголовка 1.1
## Заголовок 1.2
Здесь текст для заголовка 1.2
### Заголовок 1.2.1
Здесь текст для заголовка 1.2.1
### Заголовок 1.2.2
Здесь текст для заголовка 1.2.2
# Заголовок 2
Здесь текст для заголовка 2
## Заголовок 2.1
Здесь текст для заголовка 2.1
## Заголовок 2.2
Здесь текст для заголовка 2.2
    """
    tree = build_markdown_tree(text, 2)
    assert restore_markdown_from_tree(tree) == text
