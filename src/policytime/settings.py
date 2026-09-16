"""Validate runtime configuration once, at the application boundary."""

from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="POLICYTIME_",
        env_file=".env",
        extra="ignore",
        frozen=True,
    )
    mode: Literal["demo", "live"] = "demo"
    corpus_dir: Path = Path("corpus")
    database_url: str = (
        "postgresql+psycopg://policytime:local-development-only@localhost:5432/policytime"
    )
    mistral_api_key: SecretStr = Field(
        default=SecretStr(""),
        validation_alias=AliasChoices("MISTRAL_API_KEY", "POLICYTIME_MISTRAL_API_KEY"),
    )
    model_cache: Path = Path(".cache/models")
    monthly_budget_usd: Annotated[Decimal, Field(gt=0, le=10)] = Decimal("10")
    metrics_token: SecretStr = SecretStr("")
    allowed_hosts: tuple[str, ...] = ("localhost", "127.0.0.1", "testserver")
    requests_per_minute: Annotated[int, Field(ge=1, le=120)] = 10
    concurrency: Annotated[int, Field(ge=1, le=4)] = 2
    provider_timeout_seconds: Annotated[float, Field(gt=0, le=25)] = 20

    @model_validator(mode="after")
    def require_live_dependencies(self) -> Self:
        if self.mode != "live":
            return self
        if not self.mistral_api_key.get_secret_value():
            raise ValueError("Live mode requires MISTRAL_API_KEY.")
        if len(self.metrics_token.get_secret_value()) < 24:
            raise ValueError("Live mode requires a metrics token of at least 24 characters.")
        if not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError("Live mode requires PostgreSQL via psycopg.")
        return self
