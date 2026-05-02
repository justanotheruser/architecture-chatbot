from jinja2 import Template
from chatbot.config import RAGConfig
from chatbot.llm_client import LLMClient
from chatbot.models import DataChunk
from chatbot.ports import Encoder, Index
from loguru import logger


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
        result += f"{chunk.text}"
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

    def get_answer(self, question: str) -> str:
        context_chunks = self.get_context(question)
        prompt = self.prompt_builder.build_prompt(question, context_chunks)
        answer = self.get_answer_from_llm(prompt)
        return answer

    def get_context(self, question: str) -> list[DataChunk]:
        indices = self.index.search(question, 10)
        return [self.chunks[i] for i in indices]

    def get_answer_from_llm(self, prompt: str) -> str:
        logger.info("Requesting answer from LLM: {}", prompt)
        return self._llm.complete(prompt)
