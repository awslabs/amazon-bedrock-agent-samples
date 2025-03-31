import os

from mcp import StdioServerParameters

from InlineAgent.tools import MCPStdio
from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent
from InlineAgent import AgentAppConfig

config = AgentAppConfig()

server_params = StdioServerParameters(
    command="docker",
    args=["run", "-i", "--rm", "-e", "PERPLEXITY_API_KEY", "mcp/perplexity-ask"],
    env={"PERPLEXITY_API_KEY": config.PERPLEXITY_API_KEY},
)


async def main():
    preplexity_mcp_client = await MCPStdio.create(server_params=server_params)

    try:

        preplexity_action_group = ActionGroup(
            name="SearchActionGroup",
            mcp_clients=[preplexity_mcp_client],
        )

        await InlineAgent(
            foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            instruction="""You are a friendly assistant that is responsible for resolving user queries. """,
            agent_name="search_agent",
            action_groups=[preplexity_action_group],
        ).invoke(input_text="What is the capital of france?")

    finally:

        await preplexity_mcp_client.cleanup()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
