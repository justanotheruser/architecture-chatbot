from pydantic import BaseModel
from pathlib import Path
import yaml

_CONFIG_FOLDER = Path(__file__).parent.parent.parent / "config"


class RAGConfig(BaseModel):
    prompt: str
    chunk_size: int = 1000
    overlap_ratio: float = 0.2



def load_config(path: Path = _CONFIG_FOLDER / "rag.yml") -> RAGConfig:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
        return RAGConfig.model_validate(data)