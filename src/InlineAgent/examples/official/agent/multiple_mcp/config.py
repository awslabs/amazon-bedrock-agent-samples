from dotenv import load_dotenv
import os

from mcp import StdioServerParameters

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", None)
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", None)
AWS_REGION = os.getenv("AWS_REGION", None)
BEDROCK_LOG_GROUP_NAME = os.getenv("BEDROCK_LOG_GROUP_NAME", None)
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", None)
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", None)

if (
    not AWS_ACCESS_KEY_ID
    or not AWS_SECRET_ACCESS_KEY
    or not AWS_REGION
    or not BEDROCK_LOG_GROUP_NAME
    or not MCP_TRANSPORT
):
    raise RuntimeError("environment variable not set")

if not PERPLEXITY_API_KEY:
    raise RuntimeError("PERPLEXITY_API_KEY environment variable not set")

cost_server_params = StdioServerParameters(
    command="/usr/local/bin/docker",
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
        "MCP_TRANSPORT",
        "aws-cost-explorer-mcp:latest",
    ],
    env={
        "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
        "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
        "AWS_REGION": AWS_REGION,
        "BEDROCK_LOG_GROUP_NAME": BEDROCK_LOG_GROUP_NAME,
    },
)

perplexity_server_params = StdioServerParameters(
    command="/usr/local/bin/docker",
    args=["run", "-i", "--rm", "-e", "PERPLEXITY_API_KEY", "mcp/perplexity-ask"],
    env={"PERPLEXITY_API_KEY": PERPLEXITY_API_KEY},
)
