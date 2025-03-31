#################################################
# This example is currently under construction #
###############################################

import asyncio

from InlineAgent.agent import CollaboratorAgent, InlineAgent
from InlineAgent.knowledge_base import KnowledgeBasePlugin
from InlineAgent.types import InlineCollaboratorAgentConfig
from InlineAgent import AgentAppConfig

from tools import forecast_functions, peak_functions
from prompt import forecast_agent_instruction, peak_agent_instruction


config = AgentAppConfig()

forecast_kb = KnowledgeBasePlugin(
    name=config.FORECAST_KNOWLEDGE_BASE_NAME,
    description="Access this knowledge base when needing to explain specific forecast generation methodology.",
    profile="default",
)

forecast_agent = InlineAgent(
    foundation_model="us.anthropic.claude-3-5-sonnet-20240620-v1:0",
    instruction=forecast_agent_instruction,
    action_groups=[
        {
            "name": "CodeInterpreter",
            "builtin_tools": {"parentActionGroupSignature": "AMAZON.CodeInterpreter"},
        },
        {
            "name": "ForecastConsumption",
            "lambda_name": config.FORECAST_LAMNDA_NAME,
            "function_schema": forecast_functions,
        },
    ],
    knowledge_bases=[forecast_kb],
    agent_name="forecast_agent",
    collaborator_configuration={
        "relayConversationHistory": "TO_COLLABORATOR",
        "instruction": "Delegate energy consumption analysis and forecasting tasks to the Forecasting Agent, ensuring adherence to its specific protocols and capabilities.",
    },
)

# asyncio.run(forecast_agent.invoke(input_text="can you give me my forecasted energy consumption? How does it compare with my past energy usage? My customer id is 1"))

# forecast_agent.invoke(inputText="can you give me my past energy consumption? What is my average spending on summer months? My customer id is 1")

solar_agent = CollaboratorAgent(
    agent_name=config.SOLAR_AGENT_NAME,
    agent_alias_id=config.SOLAR_AGENT_ALIAS_ID,
    routing_instruction="""Assign solar panel-related inquiries and issues to the Solar Panel Agent, respecting its scope and support ticket protocol.""",
    relay_conversationHistory="TO_COLLABORATOR",
)

peak_agent = InlineAgent(
    foundation_model="us.anthropic.claude-3-5-sonnet-20240620-v1:0",
    instruction=peak_agent_instruction,
    agent_name="peak_agent",
    action_groups=[
        {
            "name": "PeakLoad",
            "lambda_name": config.PEAK_AGENT_LAMBDA_NAME,
            "function_schema": peak_functions,
        }
    ],
    collaborator_configuration=InlineCollaboratorAgentConfig(
        relayConversationHistory="TO_COLLABORATOR",
        instruction="Direct peak load management and energy optimization tasks to the Peak Load Manager Agent, leveraging its analytical capabilities.",
    ),
)

# asyncio.run(peak_agent.invoke(input_text="What's causing my peak load? My id is 2."))

supervisor_agent = InlineAgent(
    foundation_model="us.anthropic.claude-3-5-sonnet-20240620-v1:0",
    instruction="You are a supervisor agent that is responsible for managing the flow of the conversation.",
    collaborators=[forecast_agent, solar_agent, peak_agent],
    agent_name="supervisor_agent",
    agent_collaboration="SUPERVISOR_ROUTER",
)

asyncio.run(
    supervisor_agent.invoke(
        input_text="Can you give me my forecasted energy consumption month by month? My id is 1"
    ),
)
# # supervisor_agent.invoke(inputText="how can I check if my Sunpower double-X solar panel eletrical consumption is compliant with energy rules")
# # supervisor_agent.invoke(inputText="What's causing my peak load? My id is 2.")
# asyncio.run(supervisor_agent.invoke(
#     inputText="Can you update my forecast for month 03/2025? I will be travelling and my estimate will be 90. My id is 1. Then tell me how can I check if my Sunpower double-X solar panel eletrical consumption is compliant with energy rules?"
# ))

#################################################
# This example is currently under construction #
###############################################