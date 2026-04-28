from chatbot.chunker import Chunker
from chatbot.config import load_config
from chatbot.env import WIKI_PATH, CHUNKS_DB_PATH

if __name__ == "__main__":
    print("Preparing chunks...")
    config = load_config()
    chunker = Chunker(config.chunker)
    chunker.chunk_markdown_folder(WIKI_PATH)
    chunker.save_to_sqlite(CHUNKS_DB_PATH)