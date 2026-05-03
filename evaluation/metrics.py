from dataclasses import dataclass

from ragas.metrics.collections import (
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)


@dataclass(frozen=True)
class CollectionMetrics:
    """Набор метрик Ragas collections для одного прогона experiment."""

    faithfulness: Faithfulness
    answer_relevancy: AnswerRelevancy
    context_precision: ContextPrecision
    context_recall: ContextRecall


def build_collection_metrics(
    llm, embeddings, *, answer_relevancy_strictness: int = 3
) -> CollectionMetrics:
    return CollectionMetrics(
        faithfulness=Faithfulness(llm=llm),
        answer_relevancy=AnswerRelevancy(
            llm=llm,
            embeddings=embeddings,
            strictness=answer_relevancy_strictness,
        ),
        context_precision=ContextPrecision(llm=llm),
        context_recall=ContextRecall(llm=llm),
    )
