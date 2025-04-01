import uuid
import boto3

from InlineAgent.observability import ObservabilityConfig, observe
from InlineAgent.observability import create_tracer_provider
from InlineAgent import AgentAppConfig

observe_config = ObservabilityConfig()
agent_config = AgentAppConfig()

create_tracer_provider(config=observe_config, timeout=300)

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

    user_id = "multiagent-test"

    question = "<user-question>"

    sessionId = f"session-{str(uuid.uuid4())}"

    # Tags for filtering
    tags = ["bedrock-agent", "example", "development"]

    stream_final_response = True

    enable_trace = True  # Required for observability

    agent_answer = invoke_bedrock_agent(
        agentId=agent_config.AGENT_ID,
        agentAliasId=agent_config.AGENT_ALIAS_ID,
        inputText=question,
        sessionId=sessionId,
        enableTrace=enable_trace,
        streamingConfigurations={"streamFinalResponse": stream_final_response},
        user_id=user_id,
        tags=tags,
    )
