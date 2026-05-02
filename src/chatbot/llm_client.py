from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from chatbot.config import LLMConfig


def _chat_model(cfg: LLMConfig) -> BaseChatModel:
    vendor = cfg.vendor.lower().strip()
    if vendor == "openai":
        return ChatOpenAI(
            api_key=SecretStr(cfg.api_key),
            model=cfg.model,
            temperature=0.2,
            base_url=cfg.base_url,
        )
    raise ValueError(f"Неизвестный LLM-провайдер: {cfg.vendor!r}")


class LLMClient:
    """Вызов чат-модели по настройкам из RAG."""

    def __init__(self, cfg: LLMConfig) -> None:
        self._model = _chat_model(cfg)

    def complete(self, prompt: str) -> str:
        message = self._model.invoke([HumanMessage(content=prompt)])
        content = message.content
        return content if isinstance(content, str) else str(content)
