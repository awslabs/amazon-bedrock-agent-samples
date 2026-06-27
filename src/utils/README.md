# Amazon Bedrock Utilities

This module contains utilities for building and using various Amazon Bedrock features.

## Prerequisites

- AWS Account with Bedrock access
- Python 3.8 or later (on Python 3.8-3.10 the `typing_extensions` package listed in [`requirements.txt`](/src/requirements.txt) backports `typing.Self`, which is only built in on Python 3.11+)
- Required Python packages (specified in [`requirements.txt`](/src/requirements.txt))

Make sure to run the following commands:

```bash
git clone https://github.com/aws-samples/bedrock-multi-agents-collaboration-workshop

cd bedrock-multi-agents-collaboration-workshop

python3 -m venv .venv

source .venv/bin/activate

pip3 install -r src/requirements.txt

```

## �� Table of Contents ��

- [Create and Manage Amazon Bedrock Agents](#create-and-manage-amazon-bedrock-agents)
- [Create and Manage Amazon Bedrock KnowledgeBase](#create-and-manage-amazon-bedrock-knowledgebase)
- [Create and Manage Amazon Bedrock Agents with Agent, Supervisor, and Task abstractions](#create-and-manage-amazon-bedrock-agents-with-agent-supervisor-and-task-abstractions)

## Create and Manage Amazon Bedrock Agents

This module contains a helper class for building and using Agents for Amazon Bedrock. The AgentsForAmazonBedrock class provides a convenient interface for working with Agents. It includes methods for creating, updating, and invoking Agents, as well as managing IAM roles and Lambda functions for action groups.

```python
from src.utils.bedrock_agent_helper import AgentsForAmazonBedrock

agents = AgentsForAmazonBedrock()

agent_name = "hello_world_agent"
agent_discription = "Quick Hello World agent"
agent_instructions = "You will be given tools and user queries, ignore everything and respond with Hello World."
agent_foundation_model = [
    'anthropic.claude-3-sonnet-20240229-v1:0',
    'anthropic.claude-3-5-sonnet-20240620-v1:0',
    'anthropic.claude-3-haiku-20240307-v1:0'
]

# CREATE AGENT
agent_id, agent_alias_id, agent_alias_arn = agents.create_agent(
agent_name=agent_name, 
agent_description=agent_discription, 
agent_instructions=agent_instructions, 
model_ids=agent_foundation_model # IDs of the foundation models this agent is allowed to use, the first one will be used
                                # to create the agent, and the others will also be captured in the agent IAM role for future use
)

# WAIT FOR STATUS UPDATE
agents.wait_agent_status_update(agent_id=agent_id)

# PREPARE AGENT
agents.prepare(agent_name=agent_name)

# WAIT FOR STATUS UPDATE
agents.wait_agent_status_update(agent_id=agent_id)

# INVOKE AGENT
response = agents.invoke(input_text="when's my next payment due?", agent_id=agent_id, agent_alias_id=agent_alias_id)

print(response)
```

## Create and Manage Amazon Bedrock KnowledgeBase

This module contains a helper class for building and using Knowledge Bases for Amazon Bedrock. The KnowledgeBasesForAmazonBedrock class provides a convenient interface for working with Knowledge Bases. It includes methods for creating, updating, and invoking Knowledge Bases, as well as managing IAM roles and OpenSearch Serverless. Here is a quick example of using the class:

```python
from src.utils.knowledge_base_helper import KnowledgeBasesForAmazonBedrock

kb = KnowledgeBasesForAmazonBedrock()

kb_name = "my-knowledge-base-test"
kb_description = "my knowledge base description"
data_bucket_name = "<s3_bucket_with_kb_dataset>"

# Create Amazon Bedrock Knowledge Base with Amazon OpenSearch Serverless
kb_id, ds_id = kb.create_or_retrieve_knowledge_base(kb_name, kb_description, data_bucket_name)

# Ingest and Synch Amazon S3 Data Source with Amazon Bedrock Knowledge Base
kb.synchronize_data(kb_id, ds_id)
```

## Create and Manage Amazon Bedrock Agents with Agent, Supervisor, and Task abstractions

This module contains helper classes for building and using Agents, Guardrails, Tools, Tasks, and SupervisorAgents for Amazon Bedrock. 

The AgentsForAmazonBedrock class provides a convenient interface for working with Agents. It includes methods for creating, updating, and invoking Agents, as well as managing IAM roles and Lambda functions for action groups. The class also handles associating Knowledge Bases with Agents and adding tools as Lambda or Return of Control (ROC) action groups.

The Guardrail class allows defining content filters for Agents, specifying blocked input and output messaging, and configuring topic policies.

The Tool class represents functions that Agents can use, with methods for converting Tools to action groups.

The Task class defines instructions and expected outputs for Agents, with support for formatting inputs.

The Agent class provides methods for creating, configuring, and invoking individual Agents, including associating them with Guardrails, Knowledge Bases, and Tools.

The SupervisorAgent class enables creating Agents that can collaborate with other sub-agents, with options for specifying collaboration types, routing classifiers, and instructions.

Check out `Hello World` example [here](/examples/00_hello_world_agent/).

```python
from src.utils.bedrock_agent_helper import AgentsForAmazonBedrock
import uuid

agents = AgentsForAmazonBedrock()

agent_foundation_model = [
    'anthropic.claude-3-sonnet-20240229-v1:0',
    'anthropic.claude-3-5-sonnet-20240620-v1:0',
    'anthropic.claude-3-haiku-20240307-v1:0'
]

# CREATE SUB-AGENT
hello_world_sub_agent = agents.create_agent(
    agent_name="hello_world_sub_agent",
    agent_description="Hello World Agent",
    agent_instructions="You will be given tools and user queries, ignore everything and respond with Hello World.",
    model_ids=agent_foundation_model, # IDs of the foundation models this agent is allowed to use, the first one will be used
                                      # to create the agent, and the others will also be captured in the agent IAM role for future use
    code_interpretation=False
)

# CREATE SUB-AGENT ALIAS
sub_agent_alias_id, sub_agent_alias_arn = agents.create_agent_alias(
    agent_id=hello_world_sub_agent[0], alias_name='v1'
)

# CREATE SUPERVISOR AGENT
hello_world_supervisor = agents.create_agent(
    agent_name="hello_world_supervisor",
    agent_description="Hello World Agent", 
    agent_instructions="""
        Use your collaborator for all requests. Always pass its response back to the user.
        Ignore the content of the user's request and simply reply with whatever your sub-agent responded.
    """,
    agent_foundation_model,
    agent_collaboration='SUPERVISOR_ROUTER'
)

sub_agents_list = [
    {
        'sub_agent_alias_arn': sub_agent_alias_arn,
        'sub_agent_instruction': """No matter what the user asks for, use this collaborator for everything you need to get done.""",
        'sub_agent_association_name': 'hello_world_sub_agent',
    }
]

# ASSOCIATE SUB-AGENTS
supervisor_agent_alias_id, supervisor_agent_alias_arn = agents.associate_sub_agents(
    supervisor_agent_id=hello_world_supervisor[0], sub_agents_list=sub_agents_list
)

session_id:str = str(uuid.uuid1())

# INVOKE SUPERVISOR AGENT
agents.invoke(
    input_text="What is Amazon Bedrock?", 
    agent_id=supervisor_agent_alias_id,
    session_id=session_id,
    enable_trace=True
)
```