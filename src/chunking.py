import pathlib
import re

def chunk_markdown(text: str) -> dict[str, str]:
    chunks = {}
    current_chunk = []
    current_title = ""

    def flush_chunk():
        nonlocal current_chunk, current_title
        if current_chunk:
            chunks[current_title] = "\n".join(current_chunk)
        current_chunk = []
        current_title = ""

    for line in text.split("\n"):
        if match := re.match(r"##[#]?\s*(?P<title>.*)", line):
            flush_chunk()
            current_title = match.group("title")
        else:
            current_chunk.append(line)
    flush_chunk()
    return chunks
        

wiki_path = pathlib.Path(__file__).parent.parent / "wiki" / "wiki"
for file in wiki_path.glob("*.md"):
    text = file.read_text(encoding="utf-8")
    chunks = chunk_markdown(text)
    print("Max chunk length: ", max(len(chunk) for chunk in chunks.values()))


