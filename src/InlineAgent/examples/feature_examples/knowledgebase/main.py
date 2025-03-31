import asyncio
from InlineAgent.knowledge_base import KnowledgeBasePlugin
from InlineAgent.agent import InlineAgent

restaurant_kb = KnowledgeBasePlugin(
    name="restaurant-kb",
    description="Use this knowledgebase to get information about restaurants menu.",
    additional_props={
        "retrievalConfiguration": {"vectorSearchConfiguration": {"numberOfResults": 5}}
    },
)


asyncio.run(
    InlineAgent(
        foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        instruction="You are a restaurant assistant helping ‘The Regrettable Experience’ handle reservations. You can talk about the restaurant menus. If customers ask anything related to reservations please ask the customer to call: +1 999 999 99 9999.",
        knowledge_bases=[restaurant_kb],
        agent_name="restaurant_agent",
        user_input=True,
    ).invoke(
        input_text="What are the deserts in dinner menu?",
        add_citation=True,
        streaming_configurations={"streamFinalResponse": True},
    )
)
