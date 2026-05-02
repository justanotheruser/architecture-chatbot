from pydantic_settings import (
    BaseSettings,
    YamlConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from pydantic import BaseModel
from pathlib import Path


_CONFIG_FOLDER = Path(__file__).parent.parent.parent / "config"
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class ChunkerConfig(BaseModel):
    wiki_path: Path
    chunks_db_path: Path
    chunk_size: int
    overlap_ratio: float


class EncoderConfig(BaseModel):
    model_name: str


class IndexConfig(BaseModel):
    indexes_dir: Path


class LLMConfig(BaseModel):
    vendor: str
    api_key: str
    base_url: str | None = None
    model: str


class RAGConfig(BaseSettings):
    chunker: ChunkerConfig
    encoder: EncoderConfig
    index: IndexConfig
    llm: LLMConfig
    prompt: str

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        yaml_file=_CONFIG_FOLDER / "rag.yml",
        yaml_file_encoding="utf-8",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            dotenv_settings,
            env_settings,
            init_settings,
            YamlConfigSettingsSource(settings_cls),
        )
