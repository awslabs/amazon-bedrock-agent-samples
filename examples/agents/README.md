# Amazon Bedrock Agent Examples

This repository is designed to get you started with Amazon Bedrock Agents by providing a set of examples that demonstrate how to orchestrate agentic workflows.

## Examples

- [Analyst assistant using Code Interpretation](/examples/agents/agent_with_code_interpretation/): Create an analyst assistant agent that can generate and execute python code to analyze different data files using the Bedrock Agents code interpretation capabilities
- [Agent using Amazon Bedrock Guardrails](/examples/agents/agent_with_guardrails_integration/): Create a banking assistant agent that integrates with an Amazon Bedrock Guardrail with a topic deny for investment advice
- [Agent using Amazon Bedrock Knowledge Bases](/examples/agents/agent_with_knowledge_base_integration/): Create an agent for customer support for solar panel maintenance
- [Agent with long term memory](/examples/agents/agent_with_long_term_memory/): Create an agent for a travel assistant use case that has memory retention capabilities
- [Agent using models not yet optimized for Bedrock Agents](/examples/agents/agent_with_models_not_yet_optimized_for_bedrock_agents/): Agents examples for models where the pre-processing, orchestration, knowledge base and post-processing prompts have not yet been optimized for Bedrock Agents
- [AWS CDK Agent](/examples/agents/cdk_agent/): define and deploy a Bedrock Agent using AWS CDK
- [Computer use Agent](/examples/agents/computer_use/): Computer use agent demo that provides the critical orchestration layer that transforms computer use from a perception capability into actionable automation
- [Custom orchestration Agent](/examples/agents/custom_orchestration_agent/): Create advanced agents using the custom orchestration functionality of Bedrock Agent
- [Configure an inline agent at runtime](/examples/agents/inline_agent/): Configure and run agents at runtime with inline agents
- [Utilize LangChain Tools with Amazon Bedrock Inline Agents](./langchain_tools_with_inline_agent/): In this code example we will orchestrate a workflow that utilizes LangChain tools like [TavilySearchResults](https://python.langchain.com/docs/integrations/tools/tavily_search/), [WikipediaQueryRun](https://api.python.langchain.com/en/latest/tools/langchain_community.tools.wikipedia.tool.WikipediaQueryRun.html), and [FileManagementToolkit](https://python.langchain.com/docs/integrations/tools/filesystem/), along with Amazon Bedrock Inline Agents
- [Provide conversation history to Amazon Bedrock Agents](./manage_conversation_history/): In this module, we will create an Amazon Bedrock Agent and understand how to initialize the Agent with Conversation History
- [Agent with metadata filtering](/examples/agents/metadata_filtering_amazon_bedrock_agents/): Create an agent with metadata filtering to optimize the retrieval of relevant information from a knowledge base
- [Agent using OpenAPI schema](/examples/agents/open_api_schema_agent/): Create an insurance claims assistant agent using an OpenAPI schema file for the action groups definition
- [Agents with user confirmation before action execution](/examples/agents/user_confirmation_agents/): Create agents that ask for user confirmation before executing an action from an action group
- [Agent connected house](/examples/agents/connected_house_agent/): Create an agent conected your house surveillance cameras
-- [Agents with human_in_the_loop](/examples/agents/human_in_the_loop/): Create an agent with confirmation and return-of-control capabilities.

