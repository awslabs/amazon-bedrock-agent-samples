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
KB_ID = os.getenv("KB_ID", None)
if (
    not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not AWS_REGION
):
    raise RuntimeError("environment variable not set")


async def main():


    kb_mcp_client = await MCPStdio.create(server_params=StdioServerParameters(
        command="docker",
        args=[ "run", "-i", "--rm", "-e", "AWS_ACCESS_KEY_ID", "-e", "AWS_SECRET_ACCESS_KEY", "-e", "AWS_REGION", "mcp/aws-kb-retrieval-server" ],
        env={
            "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
            "AWS_REGION": AWS_REGION
        }
    ))
    try:
        search_action_group = ActionGroup(
            name="SearchActionGroup",
            mcp_client=[kb_mcp_client],
        )
        await InlineAgent(
            foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            instruction=f"""You are a friendly assistant that is responsible for resolving user queries. Search the knowledge base  with id {KB_ID}.""",
            agent_name="search_agent",
            action_groups=[
                search_action_group,
            ],
        ).invoke(
            input_text=f"What is the weekend special?"
        )
    finally:
        await kb_mcp_client.cleanup()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
