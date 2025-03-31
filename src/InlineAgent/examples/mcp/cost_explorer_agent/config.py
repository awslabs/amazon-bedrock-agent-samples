from dotenv import load_dotenv
import os

from mcp import StdioServerParameters

from InlineAgent import AgentAppConfig

config = AgentAppConfig()

cost_server_params = StdioServerParameters(
    command="docker",
    args=[
        "run",
        "-i",
        "--rm",
        "-e",
        "AWS_ACCESS_KEY_ID",
        "-e",
        "AWS_SECRET_ACCESS_KEY",
        "-e",
        "AWS_REGION",
        "-e",
        "BEDROCK_LOG_GROUP_NAME",
        "-e",
        "stdio",
        "aws-cost-explorer-mcp:latest",
    ],
    env={
        "AWS_ACCESS_KEY_ID": config.AWS_ACCESS_KEY_ID,
        "AWS_SECRET_ACCESS_KEY": config.AWS_SECRET_ACCESS_KEY,
        "AWS_REGION": config.AWS_REGION,
        "BEDROCK_LOG_GROUP_NAME": config.BEDROCK_LOG_GROUP_NAME,
    },
)

perplexity_server_params = StdioServerParameters(
    command="docker",
    args=["run", "-i", "--rm", "-e", "PERPLEXITY_API_KEY", "mcp/perplexity-ask"],
    env={"PERPLEXITY_API_KEY": config.PERPLEXITY_API_KEY},
)
