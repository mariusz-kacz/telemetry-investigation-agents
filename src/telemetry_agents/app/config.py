from functools import lru_cache
from typing import Literal
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import SettingsConfigDict, BaseSettings

from telemetry_agents.shared.paths import PROJECT_ROOT
from telemetry_agents.shared.tracing import TracingExporter


class Settings(BaseSettings):
    demo_provider: Literal["fake", "azure"] = "fake"
    azure_openai_endpoint: str | None = None
    azure_openai_hypothesis_deployment_name: str | None = None
    azure_openai_evaluation_deployment_name: str | None = None
    data_root: Path
    eval_data_root: Path
    tracing_enabled: bool = False
    tracing_exporter: TracingExporter = "console"
    otlp_endpoint: str | None = None
    checkpoint_db_path: Path
    run_registry_db_path: Path

    @field_validator("data_root", mode="after")
    @classmethod
    def resolve_incident_data_dir(cls, value: Path) -> Path:
        if not value.is_absolute():
            value = PROJECT_ROOT / value

        value = value.resolve()

        if not value.exists():
            raise ValueError(f"Incident data directory does not exist: {value}")

        if not value.is_dir():
            raise ValueError(f"Incident data path is not a directory: {value}")

        return value

    @field_validator("eval_data_root", mode="after")
    @classmethod
    def resolve_eval_data_dir(cls, value: Path) -> Path:
        if not value.is_absolute():
            value = PROJECT_ROOT / value

        value = value.resolve()

        if not value.exists():
            raise ValueError(f"Eval data directory does not exist: {value}")

        if not value.is_dir():
            raise ValueError(f"Eval data path is not a directory: {value}")

        return value

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_prefix="TELEMETRY_AGENTS_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]


def require_azure_setting(value: str | None, setting_name: str) -> str:
    if value is None or not value.strip():
        raise ValueError(f"{setting_name} is required when Azure OpenAI is enabled")
    return value
