from chatbot.rag import RAG
from pathlib import Path
from chatbot.config import ChunkerConfig, RAGConfig
from pydantic import BaseModel
from chatbot.index.faiss import FaissIndex
from chatbot.encoder.sentence_transformer import SentenceTransformerEncoder
from chatbot.chunker.wiki_json_chunker import WikiJsonChunker
from chatbot.models import DataChunk
import dict_hash


def chat_loop(rag: RAG):
    print("Задайте вопрос")
    while True:
        question = input()
        if question == "exit":
            break
        answer = rag.get_answer(question)
        print(answer)


def load_chunks(cfg: ChunkerConfig) -> list[DataChunk]:
    if cfg.chunks_db_path.exists():
        return WikiJsonChunker.load_from_sqlite(cfg.chunks_db_path)
    else:
        chunker = WikiJsonChunker(cfg)
        chunker.chunk_folder(cfg.wiki_path)
        chunker.save_to_sqlite(cfg.chunks_db_path)
        return chunker.chunks


def get_index_file_path(cfg: RAGConfig) -> Path:
    def get_hashable_dict(config: dict) -> dict:
        for key, value in config.items():
            if isinstance(value, Path):
                config[key] = str(value)
            elif isinstance(value, dict):
                config[key] = get_hashable_dict(value)
            elif isinstance(value, list):
                config[key] = [get_hashable_dict(item) for item in value]

        return config

    def get_hash(config: BaseModel) -> str:
        return dict_hash.sha256(get_hashable_dict(config.model_dump()))

    encoder_settings_hash = get_hash(cfg.encoder)
    index_settings_hash = get_hash(cfg.index)
    index_file_name = (
        cfg.index.indexes_dir / f"{encoder_settings_hash}_{index_settings_hash}.bin"
    )
    return index_file_name


if __name__ == "__main__":
    cfg = RAGConfig()  # type: ignore[call-arg]
    chunks = load_chunks(cfg.chunker)
    encoder = SentenceTransformerEncoder(cfg.encoder.model_name)
    index = FaissIndex(encoder, cfg.index)
    index_file_name = get_index_file_path(cfg)
    if not index.read_index(index_file_name):
        index.add([chunk.text for chunk in chunks])
        index.write_index(index_file_name)
    rag = RAG(cfg, chunks, encoder=encoder, index=index)
    chat_loop(rag)
