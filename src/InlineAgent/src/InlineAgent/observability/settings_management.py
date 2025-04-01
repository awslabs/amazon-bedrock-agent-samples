from pydantic import HttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class ObservabilityConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    API_URL: Optional[HttpUrl] = None
    PROJECT_NAME: str = Field(default="bedrock-agent")
    ENVIRONMENT: str = Field(default="dev")
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    BEDROCK_AGENT_TRACER_NAME: str = Field(default="bedrock-agent-tracer")
    PRODUCE_BEDROCK_OTEL_TRACES: bool = Field(default=False)
