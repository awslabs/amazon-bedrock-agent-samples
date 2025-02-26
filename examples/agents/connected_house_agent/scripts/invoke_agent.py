#!/usr/bin/env python3
import boto3
import time
import argparse

from datetime import datetime, timezone


def get_completion_from_response(response):
    completion = ""

    for event in response.get("completion"):
        chunk = event["chunk"]
        completion = completion + chunk["bytes"].decode()

    return completion


def invoke_agent(agent_id, alias_id, region, query):
    # Create Bedrock Agent runtime client
    bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=region)

    session_id = str(int(time.time()))  # Use timestamp as session ID

    current_utc = datetime.now(timezone.utc)

    prompt = f"""
The current time is: {current_utc}

Below is the users query or task. Complete it and answer it consicely and to the point:
{query}
"""

    try:
        # Invoke the agent
        response = bedrock_agent.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=session_id,
            inputText=prompt,
        )

        print(get_completion_from_response(response))

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Invoke Bedrock agent")
    parser.add_argument("--agent-id", required=True, help="Bedrock agent ID")
    parser.add_argument("--alias-id", required=True, help="Bedrock agent alias ID")
    parser.add_argument("--region", required=True, help="AWS region")
    parser.add_argument("--query", required=True, help="Query to send to the agent")

    args = parser.parse_args()
    invoke_agent(args.agent_id, args.alias_id, args.region, args.query)
