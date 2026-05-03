from evaluation.main import run_evaluation_experiment
from chatbot.config import RAGConfig
from evaluation.config import EvaluationConfig
from typing import Generator, Any
from evaluation.utils import save_results


def change_use_top_k_chunks(
    from_value: int, to_value: int, step: int = 1
) -> Generator[tuple[RAGConfig, dict[str, float]], Any, Any]:
    eval_cfg = EvaluationConfig()  # type: ignore[call-arg]
    rag_cfg = RAGConfig()  # type: ignore[call-arg]
    for use_top_k_chunks in range(from_value, to_value, step):
        rag_cfg.use_top_k_chunks = use_top_k_chunks
        _, summary = run_evaluation_experiment(rag_cfg, eval_cfg)
        yield rag_cfg, summary


if __name__ == "__main__":
    results = change_use_top_k_chunks(1, 10)
    save_results(results, "change_use_top_k_chunks.csv")
