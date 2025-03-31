from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class AgentAppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )
