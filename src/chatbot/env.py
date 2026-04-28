from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

WIKI_PATH = os.getenv("WIKI_PATH", None)
if WIKI_PATH is None:
    raise ValueError("WIKI_PATH is not set")
WIKI_PATH = Path(WIKI_PATH)

CHUNKS_DB_PATH = os.getenv("CHUNKS_DB_PATH", None)
if CHUNKS_DB_PATH is None:
    raise ValueError("CHUNKS_DB_PATH is not set")
CHUNKS_DB_PATH = Path(CHUNKS_DB_PATH)