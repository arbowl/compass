"""App config using Pydantic"""

from pathlib import Path

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database configuration"""

    path: Path = Field(default=Path("./data/metrics.db"))


class LlmConfig(BaseModel):
    """LLM provider configuration"""

    provider: str = Field(default="ollama")
    ollama_host: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="mistral:latest")
    timeout_seconds: int = Field(default=30)


class WebConfig(BaseModel):
    """Web server configuration"""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=5000)
    debug: bool = Field(default=True)


class MetricsConfig(BaseModel):
    """Metrics configuration"""

    enabled_metrics: list[str]


class AppConfig(BaseModel):
    """Main application configuration"""

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LlmConfig = Field(default_factory=LlmConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)

    class Config:
        env_prefix = "COMPASS_"


def load_config() -> AppConfig:
    """Load the application configuration from environment variables"""
    return AppConfig()
