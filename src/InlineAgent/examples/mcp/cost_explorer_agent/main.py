from InlineAgent.tools import MCPStdio
from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent

from config import cost_server_params, perplexity_server_params


async def main():

    cost_explorer_mcp_client = await MCPStdio.create(server_params=cost_server_params)

    perplexity_mcp_client = await MCPStdio.create(
        server_params=perplexity_server_params
    )

    try:
        cost_action_group = ActionGroup(
            name="CostActionGroup",
            mcp_clients=[cost_explorer_mcp_client, perplexity_mcp_client],
        )
        await InlineAgent(
            foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            instruction="""You are a friendly assistant that is responsible for resolving user queries.
            
            You have access to search, cost tool and code interpreter. 
            
            """,
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
            input_text="What is Amazon Bedrock? What are the AWS services where I spent most in last 7 days? Be pricise and create a bar graph."
        )
    finally:
        # LIFO
        await perplexity_mcp_client.cleanup()
        await cost_explorer_mcp_client.cleanup()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
