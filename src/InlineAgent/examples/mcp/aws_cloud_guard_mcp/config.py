from dotenv import load_dotenv
import os
from mcp import StdioServerParameters

from InlineAgent import AgentAppConfig

config = AgentAppConfig()
print(f"config: {config}")

# Docker-based MCP server parameters for monitoring server
monitoring_server_params = StdioServerParameters(
    command="docker",
    args=[
        "run",
        "-i",
        "--rm",
        "-e", "AWS_ACCESS_KEY_ID",
        "-e", "AWS_SECRET_ACCESS_KEY",
        "-e", "AWS_REGION",
        "-e", "BEDROCK_LOG_GROUP",
        "-e", "stdio",
        "aws-cloudguard-mcp:latest",
        "server_scripts/monitoring_agent_server.py"
    ],
    env={
        "AWS_ACCESS_KEY_ID": str(config.AWS_ACCESS_KEY_ID),
        "AWS_SECRET_ACCESS_KEY": str(config.AWS_SECRET_ACCESS_KEY),
        "AWS_REGION": str(config.AWS_REGION),
        "BEDROCK_LOG_GROUP": str(config.BEDROCK_LOG_GROUP),
    }
)

# Docker-based MCP server parameters for Jira server
jira_server_params = StdioServerParameters(
    command="docker",
    args=[
        "run",
        "-i",
        "--rm",
        "-e", "JIRA_API_TOKEN",
        "-e", "JIRA_USERNAME", 
        "-e", "JIRA_INSTANCE_URL",
        "-e", "JIRA_CLOUD",
        "-e", "PROJECT_KEY",
        "-e", "stdio",
        "aws-jira-mcp:latest",
        "server_scripts/diagnosis_agent_server.py"
    ],
    env={
        "JIRA_API_TOKEN": str(config.JIRA_API_TOKEN),
        "JIRA_USERNAME": str(config.JIRA_USERNAME),
        "JIRA_INSTANCE_URL": str(config.JIRA_INSTANCE_URL),
        "JIRA_CLOUD": str(config.JIRA_CLOUD),
        "PROJECT_KEY": str(config.PROJECT_KEY),
    }
)