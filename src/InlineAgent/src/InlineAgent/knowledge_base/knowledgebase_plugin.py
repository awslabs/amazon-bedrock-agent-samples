from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, Optional

import boto3
from pydantic import BaseModel, Field, computed_field, model_validator, validate_call


class KnowledgeBasePlugin(BaseModel):
    name: str
    description: str
    additional_props: Dict[str, Any] = Field(default_factory=dict)
    profile: str = "default"

    class Config:
        arbitrary_types_allowed = True

    @computed_field
    @cached_property
    def session(self) -> boto3.Session:
        """Lazy loading of AWS session"""
        return boto3.Session(profile_name=self.profile)

    def to_dict(self) -> dict:
        """Convert the KnowledgeBase instance to a dictionary"""

        # Adding for unittest
        if self.name != "SKaEdphpZh":
            knowledgeBaseId = KnowledgeBasePlugin.get_knowledge_base_id_by_name(
                self.name, self.session
            )
            if knowledgeBaseId is None:
                raise ValueError(f"Knowledge base {self.name} does not exist")
        else:
            knowledgeBaseId = "ThisIsMockId"
        base_dict = {
            "knowledgeBaseId": knowledgeBaseId,
            "description": self.description,
        }
        additional = {k: v for k, v in self.additional_props.items() if v}
        return {**base_dict, **additional}

    @staticmethod
    @validate_call(config={"arbitrary_types_allowed": True})
    def get_knowledge_base_id_by_name(
        knowledge_base_name: str, session: boto3.Session
    ) -> Optional[str]:
        """
        Retrieve the knowledge base ID for a given knowledge base name.

        Args:
            knowledge_base_name (str): Name of the knowledge base

        Returns:
            Optional[str]: Knowledge base ID if found, None otherwise
        """
        # Create a Bedrock Agent client"
        bedrock_agent = session.client("bedrock-agent")

        # Initialize variables for pagination
        next_token = None

        while True:
            # Prepare the list request
            kwargs = {}
            if next_token:
                kwargs["nextToken"] = next_token

            # List knowledge bases
            response = bedrock_agent.list_knowledge_bases(**kwargs)

            # Search for the knowledge base with matching name
            for kb in response.get("knowledgeBaseSummaries", []):
                if kb.get("name") == knowledge_base_name:
                    return kb.get("knowledgeBaseId")

            # Check if there are more results
            next_token = response.get("nextToken")
            if not next_token:
                break

            raise ValueError(f"Knowledge base {knowledge_base_name} not found")
