import asyncio
import uuid

from InlineAgent.agent import CollaboratorAgent, InlineAgent
from InlineAgent.knowledge_base import KnowledgeBasePlugin
from InlineAgent.types import InlineCollaboratorAgentConfig
from InlineAgent import AgentAppConfig
from mcp import StdioServerParameters

from InlineAgent.tools import MCPStdio
from InlineAgent.action_group import ActionGroup
from tools import forecast_functions, peak_functions
from prompt import forecast_agent_instruction, peak_agent_instruction

config = AgentAppConfig()

forecast_agent = CollaboratorAgent(
    agent_name=config.FORECAST_AGENT_NAME,
    agent_alias_id=config.FORECAST_AGENT_ALIAS_ID,
    routing_instruction="""Delegate energy consumption analysis and forecasting tasks to the Forecasting Agent, ensuring adherence to its specific protocols and capabilities.""",
    relay_conversationHistory="TO_COLLABORATOR",
)

solar_agent = CollaboratorAgent(
    agent_name=config.SOLAR_AGENT_NAME,
    agent_alias_id=config.SOLAR_AGENT_ALIAS_ID,
    routing_instruction="""Assign solar panel-related inquiries and issues to the Solar Panel Agent, respecting its scope and support ticket protocol.""",
    relay_conversationHistory="TO_COLLABORATOR",
)

peak_agent = CollaboratorAgent(
    agent_name=config.PEAK_AGENT_NAME,
    agent_alias_id=config.PEAK_AGENT_ALIAS_ID,
    routing_instruction="""Direct peak load management and energy optimization tasks to the Peak Load Manager Agent, leveraging its analytical capabilities.""",
    relay_conversationHistory="TO_COLLABORATOR",
)

async def main():
    server_params = StdioServerParameters(
        command="docker",
        args=["run", "-i", "--rm", "-e", "PERPLEXITY_API_KEY", "mcp/perplexity-ask"],
        env={"PERPLEXITY_API_KEY": config.PERPLEXITY_API_KEY},
    )

    preplexity_mcp_client = await MCPStdio.create(server_params=server_params)
    
    preplexity_action_group = ActionGroup(
        name="SearchActionGroup",
        description="This action group is responsible for searching the internet for information.",
        mcp_clients=[preplexity_mcp_client],
    )
    try:
        

        supervisor = InlineAgent(
            foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            instruction="You are a supervisor agent that is responsible for managing the flow of the conversation. You can using preplexity to search the web.",
            agent_name="supervisor_agent",
            action_groups=[preplexity_action_group],
            collaborators=[forecast_agent, solar_agent, peak_agent],
            agent_collaboration="SUPERVISOR",
        )
        
        session_id = str(uuid.uuid4())
        
        while True:
            user_query = input("Assistant: How can I help you?\n")

            await supervisor.invoke(
                input_text=user_query,
                session_id=session_id
            )

    finally:

        await preplexity_mcp_client.cleanup()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())