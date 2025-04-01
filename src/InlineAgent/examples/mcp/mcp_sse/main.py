from dotenv import load_dotenv
import os

from InlineAgent.tools.mcp import MCPHttp, MCPStdio
from mcp import StdioServerParameters

from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent
from InlineAgent import AgentAppConfig


config = AgentAppConfig()


async def main():

    cost_explorer_mcp_client = await MCPHttp.create(url=config.MCP_SSE_URL)
    try:
        cost_action_group = ActionGroup(
            name="CostActionGroup",
            mcp_clients=[cost_explorer_mcp_client],
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
