"""
Bedrock Agents module for interacting with Amazon Bedrock Agents.

This package provides functionality for working with Amazon Bedrock Agents,
allowing users to create, manage, and interact with AI agents powered by
Amazon Bedrock.
"""

from .action_group import ActionGroup, ActionGroups
from .agent import InlineAgent, CollaboratorAgent, require_confirmation
from .knowledge_base import knowledgebase_plugin
from .constants import USER_INPUT_ACTION_GROUP_NAME, TraceColor, Level
from .utils import AgentAppConfig
from .observability import *
from .tools import *
from .types import *
from . import _version

__version__ = _version.get_versions()["version"]
