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

    def complete(self, prompt: str) -> tuple[str, int, int]:
        """Ответ, prompt tokens, completion tokens (из usage_metadata провайдера, иначе 0)."""
        message = self._model.invoke([HumanMessage(content=prompt)])
        content = message.content
        text = content if isinstance(content, str) else str(content)
        usage = getattr(message, "usage_metadata", None) or {}
        prompt_tokens = int(usage.get("input_tokens") or 0)
        completion_tokens = int(usage.get("output_tokens") or 0)
        return text, prompt_tokens, completion_tokens
