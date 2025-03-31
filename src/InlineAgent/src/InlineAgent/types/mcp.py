from typing import List, Literal
from pydantic import BaseModel, Field
from pathlib import Path


class MCPConfig(BaseModel):
    class Config:
        extra = "forbid"
        arbitrary_types_allowed = True

    command: str
    """The executable to run to start the server."""

    args: list[str] = Field(default_factory=list)
    """Command line arguments to pass to the executable."""

    env: dict[str, str] | None = None
    """
    The environment to use when spawning the process.

    If not specified, the result of get_default_environment() will be used.
    """
