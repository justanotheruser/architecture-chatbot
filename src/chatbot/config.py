from pydantic import BaseModel
from pathlib import Path
from chatbot.chunker import ChunkerConfig
import yaml


_CONFIG_FOLDER = Path(__file__).parent.parent.parent / "config"


class RAGConfig(BaseModel):
    chunker: ChunkerConfig
    prompt: str


def load_config(path: Path = _CONFIG_FOLDER / "rag.yml") -> RAGConfig:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
        return RAGConfig.model_validate(data)
