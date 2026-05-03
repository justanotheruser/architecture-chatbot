from matplotlib import pyplot as plt
import sys
import pandas as pd
from pathlib import Path
from evaluation.main import run_evaluation_experiment
from chatbot.config import RAGConfig
from evaluation.config import EvaluationConfig
from typing import Generator, Any
from evaluation.utils import save_results, RESULTS_DIR


RESULTS_FILENAME = "change_use_top_k_chunks.csv"
FROM_VALUE = 1
TO_VALUE = 8


def run_experiment(
    from_value: int, to_value: int, step: int = 1
) -> Generator[tuple[RAGConfig, dict[str, float]], Any, Any]:
    eval_cfg = EvaluationConfig()  # type: ignore[call-arg]
    rag_cfg = RAGConfig()  # type: ignore[call-arg]
    for use_top_k_chunks in range(from_value, to_value + 1, step):
        rag_cfg.use_top_k_chunks = use_top_k_chunks
        _, summary = run_evaluation_experiment(rag_cfg, eval_cfg)
        yield rag_cfg, summary


def plot_results(filename: str) -> None:
    df = pd.read_csv(Path(RESULTS_DIR) / filename)
    plot_answer_quality_metrics(df)
    plot_token_metrics(df)
    plot_time_metrics(df)


def plot_answer_quality_metrics(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    for metric in [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    ]:
        ax.plot(df["use_top_k_chunks"], df[metric], label=metric)
    ax.legend()
    ax.set_xlabel("Number of chunks")
    ax.set_ylabel("Metric")
    ax.set_title("Anser quality metrics vs. Number of chunks")
    plt.show()


def plot_token_metrics(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    for metric in [
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
    ]:
        ax.plot(df["use_top_k_chunks"], df[metric], label=metric)
    ax.legend()
    ax.set_xlabel("Number of chunks")
    ax.set_ylabel("Metric")
    ax.set_title("Token metrics vs. Number of chunks")
    plt.show()


def plot_time_metrics(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    for metric in [
        "total_latency",
        "context_latency",
        "generation_latency",
    ]:
        ax.plot(df["use_top_k_chunks"], df[metric], label=metric)
    ax.legend()
    ax.set_xlabel("Number of chunks")
    ax.set_ylabel("Metric")
    ax.set_title("Time metrics vs. Number of chunks")
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python change_use_top_k_chunks.py [run | plot]")
        sys.exit(1)
    if sys.argv[1] == "run":
        results = run_experiment(FROM_VALUE, TO_VALUE)
        save_results(results, RESULTS_FILENAME)
    elif sys.argv[1] == "plot":
        plot_results(RESULTS_FILENAME)
    else:
        print("Usage: python change_use_top_k_chunks.py [run | plot]")
        sys.exit(1)
