import pandas as pd
from chatbot.config import RAGConfig
from typing import Generator, Any
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"


def convert_to_result_row(
    rag_cfg: RAGConfig, summary: dict[str, float]
) -> dict[str, Any]:
    rag_cfg_columns = {
        "chunk_size": rag_cfg.chunker.chunk_size,
        "overlap_ratio": rag_cfg.chunker.overlap_ratio,
        "use_top_k_chunks": rag_cfg.use_top_k_chunks,
        "vendor": rag_cfg.llm.vendor,
        "llm_model": rag_cfg.llm.model,
        "embeddings_model": rag_cfg.encoder.model_name,
    }
    return {**rag_cfg_columns, **summary}


def save_results(
    results: Generator[tuple[RAGConfig, dict[str, float]], Any, Any], filename: str
) -> None:
    df = pd.DataFrame(
        [convert_to_result_row(rag_cfg, summary) for rag_cfg, summary in results]
    )
    df.to_csv(RESULTS_DIR / filename, index=False)
