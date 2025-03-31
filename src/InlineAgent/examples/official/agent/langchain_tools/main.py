import asyncio
import os
import json
from dotenv import load_dotenv

from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_community.utilities.github import GitHubAPIWrapper

from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent

load_dotenv()

github = GitHubAPIWrapper()

tools = [github.get_issues, github.get_pull_request]

github_action_group = ActionGroup(name="github_action_group", tools=tools)

github_agent = InlineAgent(
    foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    instruction="""You are a friendly assistant that is responsible for getting issues and PRs of Github Repository """,
    agent_name="cost_agent",
    action_groups=[
        github_action_group,
        {
            "name": "CodeInterpreter",
            "builtin_tools": {"parentActionGroupSignature": "AMAZON.CodeInterpreter"},
        },
    ],
)

asyncio.run(
    github_agent.invoke("What are the issues in the repo? Create a excel file for it")
)
