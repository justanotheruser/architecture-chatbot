from jinja2 import Template
from chatbot.config import RAGConfig
from chatbot.llm_client import LLMClient
from chatbot.models import DataChunk
from chatbot.ports import Encoder, Index
from loguru import logger
from dataclasses import dataclass
import time


@dataclass(slots=True)
class RAGResponse:
    answer: str
    n_context_chunks: int
    context_latency: float
    prompt_tokens: int
    completion_tokens: int
    generation_latency: float
    # ~= сумме context_latency и generation_latency, но учитывает время на составления промпта
    total_latency: float

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class PromptBuilder:
    def __init__(self, prompt_template: str):
        self.template: Template = Template(prompt_template)

    def build_prompt(self, question: str, data_chunks: list[DataChunk]) -> str:
        context = "\n".join([self.chunk_to_context(chunk) for chunk in data_chunks])
        return self.template.render(question=question, context=context)

    @staticmethod
    def chunk_to_context(chunk: DataChunk) -> str:
        result = f"Имя статьи: {chunk.page_title}\n"
        if chunk.sections:
            result += f"Заголовок раздела: {chunk.sections}\n"
        result += f"{chunk.text}\n"
        return result


class RAG:
    def __init__(
        self, config: RAGConfig, chunks: list[DataChunk], encoder: Encoder, index: Index
    ):
        self.cfg = config
        self.chunks = chunks
        self.encoder = encoder
        self.index = index
        self.prompt_builder = PromptBuilder(config.prompt)
        self._llm = LLMClient(config.llm)

    def get_answer(self, question: str) -> tuple[RAGResponse, list[DataChunk]]:
        start_time = time.time()
        context_chunks = self.get_context(question)
        context_latency = time.time() - start_time
        prompt = self.prompt_builder.build_prompt(question, context_chunks)
        generation_start_time = time.time()
        answer, prompt_tokens, completion_tokens = self.get_answer_from_llm(prompt)
        generation_end_time = time.time()
        generation_latency = generation_end_time - generation_start_time
        total_latency = generation_end_time - start_time
        return RAGResponse(
            answer=answer,
            n_context_chunks=len(context_chunks),
            context_latency=context_latency,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            generation_latency=generation_latency,
            total_latency=total_latency,
        ), context_chunks

    def get_context(self, question: str) -> list[DataChunk]:
        indices = self.index.search(question, self.cfg.use_top_k_chunks)
        return [self.chunks[i] for i in indices]

    def get_answer_from_llm(self, prompt: str) -> tuple[str, int, int]:
        logger.info("Requesting answer from LLM: {}", prompt)
        return self._llm.complete(prompt)
