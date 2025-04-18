## 4/3/2025

Added examples for agents not yet optimized with Bedrock Agents 
- [Contract Assistant Agent](/examples/multi_agent_collaboration/not_yet_optimized_models_agent/)
- [Contract Assistant Agent](/examples/agents/agent_with_models_not_yet_optimized_for_bedrock_agents/)

## 3/31/2025

Added example for contract assistant
- [Contract Assistant Agent](/examples/multi_agent_collaboration/contract_assistant_agent/)

## 12/1/2024

- Repository introduced with following examples:

1. **[Hello World Agent](/examples/multi_agent_collaboration/00_hello_world_agent/)**
2. **[DevOps Agent](/examples/multi_agent_collaboration/devops_agent/)**
3. **[Energy Efficiency Management Agent](/examples/multi_agent_collaboration/energy_efficiency_management_agent/)**
4. **[Portfolio Assistant Agent](/examples/multi_agent_collaboration/portfolio_assistant_agent/)**
5. **[Startup Advisor Agent](/examples/multi_agent_collaboration/startup_advisor_agent/)**
6. **[Sports Team Poet Agent](/examples/multi_agent_collaboration/team_poems_agent/)**
7. **[Trip Planner Agent](/examples/multi_agent_collaboration/trip_planner_agent/)**
8. **[Voyage Vituoso Agent](/examples/multi_agent_collaboration/voyage_virtuoso_agent/)**

- Repository introduced with following shared tool. Deployment is only supported with CloudFormation Stack:

1. **[File Store Tool](/src/shared/file_store/)**
2. **[Stock Data Tool](/src/shared/stock_data/)**
3. **[Web Search Tool](/src/shared/web_search/)**

- Repository introduced with bedrock_agent_helper, bedrock_agent, and knowledge_base_helper.


## 01/12/2025

Renaming examples folder for simplicity and adding documentation for single agents examples


## 1/31/2025

- Following examples added for Amazon Bedrock Agents:

1. [Analyst assistant using Code Interpretation](/examples/agents/agent_with_code_interpretation/)
2. [Agent using Amazon Bedrock Guardrails](/examples/agents/agent_with_guardrails_integration/)
3. [Agent using Amazon Bedrock Knowledge Bases](/examples/agents/agent_with_knowledge_base_integration/)
4. [Agent with long term memory](/examples/agents/agent_with_long_term_memory/)
5. [Agent using models not yet optimized for Bedrock Agents](/examples/agents/agent_with_models_not_yet_optimized_for_bedrock_agents/)
6. [AWS CDK Agent](/examples/agents/cdk_agent/)
7. [Custom orchestration Agent](/examples/agents/custom_orchestration_agent/)
8. [Configure an inline agent at runtime](/examples/agents/inline_agent/)
9. [Utilize LangChain Tools with Amazon Bedrock Inline Agents](/examples/agents/langchain_tools_with_inline_agent/)
10. [Provide conversation history to Amazon Bedrock Agents](/examples/agents/manage_conversation_history/)
11. [Agent using OpenAPI schema](/examples/agents/open_api_schema_agent/)
12. [Agents with user confirmation before action execution](/examples/agents/user_confirmation_agents/)

- [Streamlit](/examples/agents_ux/) UI demo added.


## 2/9/2025
- Following extensions added to [bedrock_agent](/src/utils/bedrock_agent.py) library 
1. Added helper methods `delete_by_name()` and `exists()` to `Agent` to allow using `bedrock_agent` for common operations without needing to use `bedrock_agent_helper` directly
2. Reworked `Tool` class
3. Added `attach_tool()` to `Agent` to allow attaching tools after creation
4. Added `attach_tool_from_function()` to Agent to create a tool from Python code with type hints (note it currently materializes a lambda from the function)
6. Added explicit `update()` and `prepare()` methods to `Agent`
7. Added `create_from_yaml()` to `Agent`, allows creating fom a definition in a YAML file

- Following documentation added for Amazon Bedrock Agents:
1. Added [Getting Started tutorial](/examples/sdk/getting_started.ipynb) for using the bedrock_agent library with basic usage examples and coverage of the new functions added below
2. All examples in [multi_agent_collaboration](examples/multi_agent_collaboration/) that used both `bedrock_agent` and `bedrock_agent_helper` have been updated to just use `bedrock_agent` with `Agent` helper functions
- Following usability improvements made to [bedrock_agent](/src/utils/bedrock_agent.py) library:
1. Renamed `direct_create()` in `Agent` and `SupervisorAgent` to `create()` for simplicity
2. When creating from YAML, `Agent` will automatically de-indent (dedent) the description
3. Agent will now automatically `prepare()` internally if needed when `invoke()`, removing a step from user code

- Following extensions added to [bedrock_agent_helper](/src/utils/bedrock_agent_helper.py) library:
1. Added `create_lambda_file()`, which will create aa Lambda function from supplied Python code with type hints


## 02/18/2025
Added to [Agent using models not yet optimized for Bedrock Agents](/examples/agents/agent_with_models_not_yet_optimized_for_bedrock_agents/) By creating a code sample for llama as an unoptimized model

## 02/26/2025
Adding [Agent with access to house security camera in cloudformation](/examples/agents/connected_house_agent/)

## 02/27/2025
[metadata-filtering-amazon-bedrock-agents](/examples/agents/metadata_filtering_amazon_bedrock_agents/)

## 03/03/2025

- Adding the following MAC example:

1. [Real Estate Investment Agent](/examples/multi_agent_collaboration/real_estate_investment_agent/)

- Adding the following shared tools. Deployment is only supported with CloudFormation Stack:

1. [Economic Data Tool](/src/shared/economic_data/)
2. [Property Data Tool](/src/shared/property_data/)


## 03/10/2025

[Computer use Agent](/examples/agents/computer_use/)

## 03/17/2025

[Human-in-the-loop Agent](/examples/agents/human_in_the_loop/)


## 03/31/2025

[Inline Agent SDK](./src/InlineAgent/)

## 04/02/2025

[Langfuse self deployment](/examples/agent_observability/deploy-langfuse-on-ecs-fargate-with-typescript-cdk/)

## 04/07/2025

**[Investment Research Agent](/examples/multi_agent_collaboration/investment_research_agent/)**

## 18/04/2025
**[Metadata filtering](/examples/multi_agent_collaboration/metadata_filtering)**
