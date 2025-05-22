# Bedrock Agent Arize-Phoenix Integration 

This package provides Phoenix observability tool for Amazon Bedrock Agents for experimentation tracking, evaluation, and troubleshooting of AI and LLM applications

## Features

- Comprehensive Traceability: Gain visibility into every step of your agent’s execution path, from initial user query through knowledge retrieval and action execution
- Systematic Evaluation Framework: Apply consistent evaluation methodologies to measure and understand agent performance
- Data-Driven Optimization: Run structured experiments to compare different agent configurations and identify optimal settings


## Hierarchy

The trace hierarchy follows this pattern:

```
L1: "agent" : "bedrock_agent.invoke_agent"
  L2: "chain" : "orchestrationTrace"
    L3: "llm" : "LLM"
    L3: "retriever" : "knowledge_base" 
    L3: "tool" : "action_group"
    L3: "llm" : "LLM"

```

## Quick Start

1. Install the required dependencies:
```bash
!pip install -q arize-phoenix-otel boto3 anthropic openinference-instrumentation-bedrock
```

2. Create a function to run your agent and capture its outputs:

```python
def run(input_text):
    session_id = f"default-session1_{int(time.time())}"

    attributes = dict(
        inputText=input_text,
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        enableTrace=True,
    )
    response = bedrock_agent_runtime.invoke_agent(**attributes)

    # Stream the response
    for _, event in enumerate(response["completion"]):
        if "chunk" in event:
            print(event)
            chunk_data = event["chunk"]
            if "bytes" in chunk_data:
                output_text = chunk_data["bytes"].decode("utf8")
                print(output_text)
        elif "trace" in event:
            print(event["trace"])

```

## Configuration

The following configuration options can be provided:

| Parameter | Description | Default |
|-----------|-------------|---------|    
| `api_key` | Phoenix api key | Environment variable or demo key |
| `PHOENIX_CLIENT_HEADERS` | Phoenix client header| "api_key=ENTER YOUR API KEY" |
| `PHOENIX_COLLECTOR_ENDPOINT` |  URL | https://app.phoenix.arize.com |
| `project_name` | Project name | Amazon Bedrock Agents |
| `userId` | User ID for Arize-phoenix | anonymous |
| `session_id` | Sessiojn Id| anonymous |
| `metadata` | custom attributes | ["key":"value"] |
| `tags` | Tags for filtering in Arize Phoenix | [] |
| `prompt_template` | Prompt Management | "" |
| `prompt_template_version` | Promot version | "" |
| `prompt_template_variables` | Custom trace ID | ["key":"value"] |
| `show_traces` | Whether to print raw trace data | False |

## Attribute Naming

This integration follows Openinference Semantic Conventions:

For a complete guide to Python semantic conventions, refer to the following link
https://docs.arize.com/arize/llm-tracing/tracing/semantic-conventions
