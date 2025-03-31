from dotenv import load_dotenv
import os

from InlineAgent.tools.mcp import MCPHttp, MCPStdio
from mcp import StdioServerParameters

from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", None)
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", None)
AWS_REGION = os.getenv("AWS_REGION", None)
BEDROCK_LOG_GROUP_NAME = os.getenv("BEDROCK_LOG_GROUP_NAME", None)
MCP_SSE_URL = os.getenv("MCP_SSE_URL", None)

if (
    not AWS_ACCESS_KEY_ID
    or not AWS_SECRET_ACCESS_KEY
    or not AWS_REGION
    or not BEDROCK_LOG_GROUP_NAME
    or not MCP_SSE_URL
):
    raise RuntimeError("environment variable not set")


async def main():

    cost_explorer_mcp_client = await MCPHttp.create(url=MCP_SSE_URL)
    try:
        cost_action_group = ActionGroup(
            name="CostActionGroup",
            mcp_client=[cost_explorer_mcp_client],
        )
        await InlineAgent(
            foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            instruction="""You are a friendly assistant that is responsible for resolving user queries related to AWS Cost. """,
            agent_name="cost_agent",
            action_groups=[
                cost_action_group,
                {
                    "name": "CodeInterpreter",
                    "builtin_tools": {
                        "parentActionGroupSignature": "AMAZON.CodeInterpreter"
                    },
                },
            ],
        ).invoke(
            input_text="What are the AWS services where I spent most in last 7 days? Be pricise and create a bar graph."
        )
    finally:
        await cost_explorer_mcp_client.cleanup()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
