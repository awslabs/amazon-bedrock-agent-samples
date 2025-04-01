import asyncio

from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent
from crewai_tools import RagTool


def pdf_search_wrapper(query: str) -> str:
    """
    Searches through Amazon 2023 Shareholder letter for information.

    Parameters:
        query(str): The search query to look for in the letter

    Returns:
        str: The search results from the letter matching the query
    """
    pdf_search_tool = RagTool(
        config=dict(
            llm=dict(
                provider="aws_bedrock",
                config=dict(
                    model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                ),
            ),
            embedder=dict(
                provider="aws_bedrock",
                config=dict(
                    model="amazon.titan-embed-text-v2:0",
                ),
            ),
        ),
    )
    return pdf_search_tool._run(query=query)


tools = [pdf_search_wrapper]

bedrock_action_group = ActionGroup(
    name="bedrock_action_group", tools=tools, argument_key="Parameters:"
)

bedrock_agent = InlineAgent(
    foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    instruction="""You are a friendly assistant that is responsible for giving information present in Amazon 2023 Shareholder Letter.""",
    agent_name="cost_agent",
    action_groups=[
        bedrock_action_group,
    ],
)

asyncio.run(bedrock_agent.invoke("What is Amazon's total revenue in 2023?"))
