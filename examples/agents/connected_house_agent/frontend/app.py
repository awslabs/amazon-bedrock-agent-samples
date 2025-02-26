import gradio as gr
import boto3
import random
import os

from datetime import datetime, timezone


REGION_NAME = os.getenv("AWS_REGION", "us-west-2")
AGENT_ALIAS = os.getenv("AGENT_ALIAS")
AGENT_ID = os.getenv("AGENT_ID")

if not AGENT_ALIAS or not AGENT_ID:
    raise ValueError("AGENT_ALIAS and AGENT_ID environment variables must be set")

bedrock_client = boto3.client(
    service_name="bedrock-agent-runtime",
    region_name=REGION_NAME,
)

# Generate random sessionId
SESSION_ID = str(random.randint(1, 100000000))


def get_completion_from_response(response):
    completion = ""

    for event in response.get("completion"):
        chunk = event["chunk"]
        completion = completion + chunk["bytes"].decode()

    return completion


def invoke_agent(message, history):
    current_utc = datetime.now(timezone.utc)
    current_utc_str = current_utc.isoformat()

    message = f"""
The current UTC time is: {current_utc_str}.
    
Below is the users query or task. Complete it and answer it consicely and to the point:
{message}
    """

    response = bedrock_client.invoke_agent(
        agentAliasId=AGENT_ALIAS,
        agentId=AGENT_ID,
        inputText=message,
        sessionId=SESSION_ID,
    )

    return get_completion_from_response(response)


if __name__ == "__main__":

    gr.ChatInterface(
        fn=invoke_agent,
        type="messages",
    ).launch(server_port=7861)
