import asyncio
import math
from typing import Any, cast

from pydantic import BaseModel, Field

from ragas.backends.inmemory import InMemoryBackend
from ragas.dataset import Dataset
from ragas.experiment import Experiment, experiment

from chatbot.config import RAGConfig
from chatbot.main import create_rag_client
from chatbot.tools.obfuscate import inverse_replace_terms_in_text, replace_terms_in_text
from chatbot.rag import RAG
from evaluation.config import EvaluationConfig
from evaluation.metrics import CollectionMetrics, build_collection_metrics
from evaluation.models import build_evaluator_models


class EvalCase(BaseModel):
    user_input: str
    reference: str


class EvalExperimentRow(EvalCase):
    """Одна строка результата experiment (вход + ответ RAG + скоры collections-метрик)."""

    response: str = ""
    retrieved_contexts: list[str] = Field(default_factory=list)
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None
    context_recall: float | None = None
    retrieved_titles: list[str] = Field(default_factory=list)
    retrieved_sections: list[str] = Field(default_factory=list)
    metric_error: str | None = None
    # Снимок с одного запроса RAG (для усреднения по датасету в CSV)
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    total_latency: float | None = None
    context_latency: float | None = None
    generation_latency: float | None = None


EVAL_DATASET: list[dict[str, str]] = [
    {
        "user_input": "Who is Corwin's father?",
        "reference": "Corwin's father is Oberon, the king of Amber.",
    },
    {
        "user_input": "What is the Pattern?",
        "reference": (
            "The Pattern is the sentient embodiment of Order that allows Amber's royal "
            "family members to walk through Shadow. In order to gain that power, "
            "a walker must walk along the Pattern to its center; stopping for too long, "
            "or leaving the pathway of the Pattern, results in a terrible death."
        ),
    },
    {
        "user_input": "Who is Corwin?",
        "reference": "Corwin is a Prince of Amber, the main character of the first five books of The Chronicles of Amber, the second son of Oberon and Faiella, and the father of Merlin.",
    },
    {
        "user_input": "Why does Benedict not simply take the throne of Amber?",
        "reference": "Benedict does not want the throne and prefers to be General of the Armies of Amber, even though his combat ability would make him almost unchallenged if he wanted it.",
    },
    {
        "user_input": "What are the Trumps of Doom?",
        "reference": "The Trumps of Doom are cards discovered by Merlin that transport the user to locations of extreme danger, effectively making them traps for the unwary.",
    },
]


def run_one_case(rag: RAG, case: dict[str, str]) -> dict[str, Any]:
    user_input = replace_terms_in_text(case["user_input"])
    response, chunk_list = rag.get_answer(user_input)
    answer = response.answer
    retrieved_contexts = [
        rag.prompt_builder.chunk_to_context(chunk) for chunk in chunk_list
    ]
    result = {
        # для оценки качества ответа
        "user_input": case["user_input"],
        "response": answer,
        "retrieved_contexts": retrieved_contexts,
        "reference": case["reference"],
        # для отладки
        "retrieved_titles": [chunk.page_title for chunk in chunk_list],
        "retrieved_sections": [chunk.sections for chunk in chunk_list],
        # для оценки стоимости и производительности
        "prompt_tokens": response.prompt_tokens,
        "completion_tokens": response.completion_tokens,
        "total_tokens": response.total_tokens,
        "total_latency": response.total_latency,
        "context_latency": response.context_latency,
        "generation_latency": response.generation_latency,
    }
    return deobfuscate_output(result)


def deobfuscate_output(output: dict[str, Any]) -> dict[str, Any]:
    output["response"] = inverse_replace_terms_in_text(output["response"])
    output["retrieved_contexts"] = [
        inverse_replace_terms_in_text(context)
        for context in output["retrieved_contexts"]
    ]
    output["retrieved_titles"] = [
        inverse_replace_terms_in_text(title) for title in output["retrieved_titles"]
    ]
    output["retrieved_sections"] = [
        inverse_replace_terms_in_text(section)
        for section in output["retrieved_sections"]
    ]
    return output


@experiment(EvalExperimentRow)
async def run_rag_eval_row(
    row: EvalCase,
    *,
    rag: RAG,
    metrics: CollectionMetrics,
) -> EvalExperimentRow:
    case = {"user_input": row.user_input, "reference": row.reference}
    try:
        out = run_one_case(rag, case)
    except Exception as e:
        return EvalExperimentRow(
            user_input=row.user_input,
            reference=row.reference,
            metric_error=f"rag_pipeline:{e!s}",
        )

    user_input = out["user_input"]
    response = out["response"]
    contexts: list[str] = out["retrieved_contexts"]
    reference = out["reference"]

    f_val = ar_val = cp_val = cr_val = None
    errors: list[str] = []

    try:
        r = await metrics.faithfulness.ascore(user_input, response, contexts)
        f_val = r.value
    except Exception as e:
        errors.append(f"faithfulness:{e!s}")

    try:
        r = await metrics.answer_relevancy.ascore(user_input, response)
        ar_val = r.value
    except Exception as e:
        errors.append(f"answer_relevancy:{e!s}")

    try:
        r = await metrics.context_precision.ascore(user_input, reference, contexts)
        cp_val = r.value
    except Exception as e:
        errors.append(f"context_precision:{e!s}")

    try:
        r = await metrics.context_recall.ascore(user_input, contexts, reference)
        cr_val = r.value
    except Exception as e:
        errors.append(f"context_recall:{e!s}")

    def _clean(x: float | None) -> float | None:
        if x is None:
            return None
        if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
            return None
        return x

    return EvalExperimentRow(
        user_input=row.user_input,
        reference=row.reference,
        response=response,
        retrieved_contexts=contexts,
        faithfulness=_clean(f_val),
        answer_relevancy=_clean(ar_val),
        context_precision=_clean(cp_val),
        context_recall=_clean(cr_val),
        retrieved_titles=out["retrieved_titles"],
        retrieved_sections=out["retrieved_sections"],
        metric_error="; ".join(errors) if errors else None,
        prompt_tokens=out.get("prompt_tokens"),
        completion_tokens=out.get("completion_tokens"),
        total_tokens=out.get("total_tokens"),
        total_latency=out.get("total_latency"),
        context_latency=out.get("context_latency"),
        generation_latency=out.get("generation_latency"),
    )


def _build_dataset(cases: list[dict[str, str]]) -> Dataset:
    backend = InMemoryBackend()
    rows = [
        EvalCase(user_input=c["user_input"], reference=c["reference"]) for c in cases
    ]
    ds = Dataset("rag_eval_input", backend, EvalCase, rows)
    ds.save()
    return ds


_SUMMARY_NUMERIC_COLS = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "total_latency",
    "context_latency",
    "generation_latency",
]


def summarize_experiment(exp: Experiment) -> dict[str, float]:
    """Средние по строкам датасета: метрики Ragas и агрегаты RAG (токены, время)."""
    df = exp.to_pandas()
    out: dict[str, float] = {}
    for c in _SUMMARY_NUMERIC_COLS:
        if c not in df.columns:
            continue
        mean_val = cast(float, df[c].mean(skipna=True))
        if mean_val != mean_val:  # NaN
            continue
        out[c] = mean_val
    return out


async def evaluate_rag_experiment(
    rag: RAG,
    cfg: EvaluationConfig,
    eval_cases: list[dict[str, str]],
    *,
    experiment_name: str = "rag-evaluation",
    answer_relevancy_strictness: int = 3,
) -> tuple[Experiment, dict[str, float]]:
    llm, embeddings = build_evaluator_models(cfg)
    m = build_collection_metrics(
        llm, embeddings, answer_relevancy_strictness=answer_relevancy_strictness
    )
    dataset = _build_dataset(eval_cases)
    exp = await run_rag_eval_row.arun(
        dataset,
        name=experiment_name,
        rag=rag,
        metrics=m,
    )
    return exp, summarize_experiment(exp)


def run_evaluation_experiment(
    rag_cfg: RAGConfig, eval_cfg: EvaluationConfig
) -> tuple[Experiment, dict[str, float]]:
    rag = create_rag_client(rag_cfg)
    exp, summary = asyncio.run(
        evaluate_rag_experiment(rag, eval_cfg, EVAL_DATASET),
    )
    return exp, summary


if __name__ == "__main__":
    rag_cfg = RAGConfig()  # type: ignore[call-arg]
    eval_cfg = EvaluationConfig()  # type: ignore[call-arg]
    exp, summary = run_evaluation_experiment(rag_cfg, eval_cfg)
    print(exp)
    print("Summary (mean over rows):", summary)
