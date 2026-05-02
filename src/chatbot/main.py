from chatbot.rag import RAG
from pathlib import Path
from chatbot.config import ChunkerConfig, RAGConfig
from pydantic import BaseModel
from chatbot.index.faiss import FaissIndex
from chatbot.encoder.sentence_transformer import SentenceTransformerEncoder
from chatbot.chunker.wiki_json_chunker import WikiJsonChunker
from chatbot.models import DataChunk
import dict_hash
from loguru import logger


def chat_loop(rag: RAG):
    print("Задайте вопрос")
    while True:
        question = input()
        if question == "exit":
            break
        answer = rag.get_answer(question)
        print(answer)


def create_or_load_chunks(cfg: ChunkerConfig) -> tuple[list[DataChunk], bool]:
    if cfg.chunks_db_path.exists():
        logger.info("Chunks database exists, loading from: {}", cfg.chunks_db_path)
        return WikiJsonChunker.load_from_sqlite(cfg.chunks_db_path), True
    else:
        logger.info("Chunks database does not exist, creating new one")
        chunker = WikiJsonChunker(cfg)
        chunker.chunk_folder(cfg.wiki_path)
        chunker.save_to_sqlite(cfg.chunks_db_path)
        return chunker.chunks, False


def create_or_load_index(
    cfg: RAGConfig, is_new_chunks: bool, encoder: SentenceTransformerEncoder, chunks: list[DataChunk]
) -> FaissIndex:
    index = FaissIndex(encoder, cfg.index)
    index_file_name = get_index_file_path(cfg)
    logger.info("Index file name: {}", index_file_name)

    is_index_loaded = False
    if not is_new_chunks:
        logger.info("Because chunks are new, we need to create new index")
    else:
        is_index_loaded = index.read_index(index_file_name)
    
    if is_index_loaded:
        logger.info("Index file loaded")
        return index
    logger.info("Adding chunks to index")
    index.add([chunk.text for chunk in chunks])
    logger.info("Writing index to file: {}", index_file_name)
    index.write_index(index_file_name)
    return index


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


def setup_logging():
    logger.add("logs/chatbot_{time}.log", rotation="100 MB", retention="10 days")


if __name__ == "__main__":
    setup_logging()
    cfg = RAGConfig()  # type: ignore[call-arg]
    logger.info("Config: {}", cfg)
    chunks, is_new_chunks = create_or_load_chunks(cfg.chunker)
    encoder = SentenceTransformerEncoder(cfg.encoder.model_name)
    index = create_or_load_index(cfg, is_new_chunks, encoder, chunks)
    rag = RAG(cfg, chunks, encoder=encoder, index=index)
    chat_loop(rag)
