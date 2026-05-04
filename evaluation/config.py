from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, AnyHttpUrl
from pathlib import Path
from pydantic_settings import PydanticBaseSettingsSource, YamlConfigSettingsSource


class EvaluationConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / ".env",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        yaml_file=Path(__file__).parent / "config.yaml",
        yaml_file_encoding="utf-8",
    )

    vendor: str
    llm_model: str
    embeddings_model: str
    api_key: SecretStr
    base_url: AnyHttpUrl | None = None

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
