from matplotlib import pyplot as plt
import sys
import pandas as pd
from pathlib import Path
from evaluation.utils import RESULTS_DIR


def main(filename: str) -> None:
    df = pd.read_csv(Path(RESULTS_DIR) / filename)

    fig, ax = plt.subplots(figsize=(10, 5))
    for metric in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
        ax.plot(df["use_top_k_chunks"], df[metric], label=metric)
    ax.legend()
    ax.set_xlabel("Number of chunks")
    ax.set_ylabel("Metric")
    ax.set_title("Anser quality metrics vs. Number of chunks")
    plt.show()


if __name__ == "__main__":
    filename = sys.argv[1]
    main(filename)