from typing import Literal, Optional
from pydantic import BaseModel


class InlineCollaboratorAgentConfig(BaseModel):
    instruction: str = str()
    relayConversationHistory: Literal["TO_COLLABORATOR", "DISABLED"] = "DISABLED"


class InlineCollaboratorConfigurations(BaseModel):
    agentAliasArn: Optional[str]
    collaboratorInstruction: str
    collaboratorName: str
    relayConversationHistory: Literal["TO_COLLABORATOR", "DISABLED"] = "DISABLED"
