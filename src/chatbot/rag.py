from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from jinja2 import Template
from chatbot.env import CHUNKS_DB_PATH
from chatbot.env import WIKI_PATH
from chatbot.chunker import Chunker
from chatbot.config import RAGConfig
from chatbot.models import DataChunk


class PromptBuilder:
    def __init__(self, prompt_template: str):
        self.template: Template = Template(prompt_template)

    def build_prompt(self, question: str, data_chunks: list[DataChunk]) -> str:
        context = "\n".join([self.chunk_to_context(chunk) for chunk in data_chunks])
        return self.template.render(question=question, context=context)
    
    @staticmethod
    def chunk_to_context(chunk: DataChunk) -> str:
        return f"""Имя файла: {chunk.file_name}
Заголовок раздела: {chunk.title}\n
{chunk.text}"""





class RAG:
    def __init__(self, config: RAGConfig):
        self.cfg = config
        self.prompt_builder = PromptBuilder(config.prompt)
        self.config = config

        self._chunks = self._load_chunks()
        self._model = SentenceTransformer("all-MiniLM-L6-v2")
        self._embeddings = self._build_embeddings()
        self._index = faiss.IndexFlatL2(self._embeddings.shape[1])
        self._index.add(self._embeddings)  # type: ignore[call-args]

    def get_answer(self, question: str) -> str:
        context_chunks = self.get_context(question)
        prompt = self.prompt_builder.build_prompt(question, context_chunks)
        answer = self.get_answer_from_llm(prompt)
        return answer

    def get_context(self, question: str) -> list[DataChunk]:
        V, I = self._index.search(self._model.encode([question]), 10)  # type: ignore[call-args]
        return [self._chunks[i] for i in I[0]]

    def get_answer_from_llm(self, prompt: str) -> str:
        return ""


    def _load_chunks(self) -> list[DataChunk]:
        if CHUNKS_DB_PATH.exists():
            return Chunker.load_from_sqlite(CHUNKS_DB_PATH)
        else:
            chunker  = Chunker(self.cfg.chunker)
            chunker.chunk_markdown_folder(WIKI_PATH)
            chunker.save_to_sqlite(CHUNKS_DB_PATH)
            return chunker.chunks
    
    def _build_embeddings(self) -> np.ndarray:
        texts = [chunk.text for chunk in self._chunks]
        return np.ascontiguousarray(self._model.encode(texts))
