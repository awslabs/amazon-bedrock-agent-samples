import os
import uuid
from InlineAgent.observability import observe
import boto3
from dotenv import load_dotenv

from InlineAgent.observability import AppConfig
from InlineAgent.observability import create_tracer_provider


@observe(show_traces=True, save_traces=False)
def invoke_bedrock_agent(inputText: str, sessionId: str, **kwargs):
    """Invoke a Bedrock Agent with instrumentation"""

    # Create Bedrock client
    profile = kwargs.pop("profile", "default")

    bedrock_agent_runtime = boto3.Session(profile_name=profile).client(
        "bedrock-agent-runtime"
    )

    # Invoke the agent with the appropriate configuration
    response = bedrock_agent_runtime.invoke_agent(
        inputText=inputText, sessionId=sessionId, **kwargs
    )

    return response


if __name__ == "__main__":

    config = AppConfig()  # Load .env variables

    create_tracer_provider(config=config, timeout=300)

    load_dotenv()

    agentId = os.environ.get("AGENT_ID")
    agentAliasId = os.environ.get("AGENT_ALIAS_ID")

    user_id = "multiagent-test"

    question = "Can you give me my past energy consumption? What is my average spending on summer months? Use code interpreter to visulize the result. My customer id is 1"

    sessionId = f"session-{str(uuid.uuid4())}"  # Dynamic session ID

    # Tags for filtering in Langfuse
    tags = ["bedrock-agent", "example", "development"]

    stream_final_response = True

    enable_trace = True  # Required for observability

    # Single invocation that works for both streaming and non-streaming
    agent_answer = invoke_bedrock_agent(
        agentId=agentId,
        agentAliasId=agentAliasId,
        inputText=question,
        sessionId=sessionId,
        enableTrace=enable_trace,
        streamingConfigurations={"streamFinalResponse": stream_final_response},
        user_id=user_id,
        tags=tags,
    )
