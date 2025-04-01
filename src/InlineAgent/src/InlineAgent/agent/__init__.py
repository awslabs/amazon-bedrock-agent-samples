"""
Bedrock Agents module for interacting with Amazon Bedrock Agents.

This package provides functionality for working with Amazon Bedrock Agents,
allowing users to create, manage, and interact with AI agents powered by
Amazon Bedrock.
"""

# Rest of your __init__.py content goes here

from .inline_agent import (
    InlineAgent,
)
from .confirmation import require_confirmation
from .process_roc import ProcessROC
from .collaborator_agent_instance import (
    CollaboratorAgent,
)

__all__ = [
    "InlineAgent",
    "require_confirmation",
    "ProcessROC",
    "CollaboratorAgent",
]
