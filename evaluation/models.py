from openai import AsyncOpenAI

from ragas.llms import llm_factory
from ragas.embeddings.base import embedding_factory

from evaluation.config import EvaluationConfig


def build_evaluator_models(cfg: EvaluationConfig):
    """LLM и эмбеддинги в modern-API (Instructor LLM + BaseRagasEmbedding) для collections."""
    api_key = cfg.api_key.get_secret_value()
    base_url = cfg.base_url.unicode_string() if cfg.base_url else None

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    evaluator_llm = llm_factory(cfg.llm_model, client=client)
    evaluator_embeddings = embedding_factory(
        cfg.vendor.lower(),
        model=cfg.embeddings_model,
        client=client,
    )

    return evaluator_llm, evaluator_embeddings
