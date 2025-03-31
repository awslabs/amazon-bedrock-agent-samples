from dataclasses import dataclass, field
from datetime import datetime, UTC

import uuid
import copy
import os
import boto3
from typing import Dict, Literal
from pydantic import Field
from termcolor import colored
from rich.console import Console
from rich.markdown import Markdown


from InlineAgent.constants import (
    TraceColor,
)
from InlineAgent.agent.process_roc import ProcessROC
from InlineAgent.observability import Trace


@dataclass
class CollaboratorAgent:
    agent_name: str
    agent_alias_id: str
    routing_instruction: str = ""
    relay_conversationHistory: Literal["TO_COLLABORATOR", "DISABLED"] = "DISABLED"
    profile: str = "default"

    @property
    def session(self) -> boto3.Session:
        """Lazy loading of AWS session"""
        return boto3.Session(profile_name=self.profile)

    @property
    def account_id(self) -> str:
        sts_client = self.session.client("sts")
        identity = sts_client.get_caller_identity()
        return identity["Account"]

    @property
    def region(self) -> str:
        return self.session.region_name

    def __post_init__(self):

        if (
            self.relay_conversationHistory != "TO_COLLABORATOR"
            and self.relay_conversationHistory != "DISABLED"
        ):
            raise ValueError(
                "relay_conversationHistory must be either 'TO_COLLABORATOR' or 'DISABLED'"
            )

        if self.agent_alias_id == "TSTALIASID":
            raise ValueError("agent_alias_id cannot be 'TSTALIASID'")

    def to_dict(self):

        agent_arn = CollaboratorAgent.get_agent_arn_by_name(
            agent_name=self.agent_name,
            region=self.region,
            account_id=self.account_id,
            session=self.session,
        )

        if self.routing_instruction == "":
            raise ValueError("routing_instruction cannot be empty")

        return {
            "agentAliasArn": f'{agent_arn.replace("agent", "agent-alias")}/{self.agent_alias_id}',
            "collaboratorInstruction": self.routing_instruction,
            "collaboratorName": self.agent_name,
            "relayConversationHistory": self.relay_conversationHistory,
        }

    @staticmethod
    def get_agent_id_by_name(agent_name: str, session: boto3.Session):
        # Create Bedrock Agent client
        bedrock_agent = session.client("bedrock-agent")

        # List all agents and find the one matching the name
        paginator = bedrock_agent.get_paginator("list_agents")

        for page in paginator.paginate():
            for agent in page["agentSummaries"]:
                if agent["agentName"] == agent_name:
                    return agent["agentId"]

        raise ValueError(f"Agent {agent_name} not found")

    @staticmethod
    def get_agent_arn_by_name(
        agent_name: str, region: str, account_id: str, session: boto3.Session
    ):

        return f"arn:aws:bedrock:{region}:{account_id}:agent/{CollaboratorAgent.get_agent_id_by_name(agent_name=agent_name, session=session)}"
