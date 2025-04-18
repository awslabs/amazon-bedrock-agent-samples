import boto3
import json
import argparse
from botocore.exceptions import *
import logging 
logger = logging.getLogger(__name__)
logger.setLevel("INFO")

def invoke_agent(agent_id, agent_alias_id, query):
    boto3_session = boto3.session.Session()
    region = boto3_session.region_name
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
    
    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=f'session-{hash(query)}',
            inputText=query
        )
        completion = ""

        for event in response.get("completion"):
            chunk = event["chunk"]
            completion = completion + chunk["bytes"].decode()

    except ClientError as e:
        logger.error(f"Couldn't invoke agent. {e}")
        raise

    return completion
        




def main():
    parser = argparse.ArgumentParser(description='Invoke Bedrock Agent')
    parser.add_argument('--agent-id', required=True, help='Agent ID to invoke')
    parser.add_argument('--agent-alias-id', required=True, help='Agent alias ID to invoke')
    parser.add_argument('--query', required=True, help='Query to send to the agent')
    
    args = parser.parse_args()
    
    response = invoke_agent(args.agent_id, args.agent_alias_id, args.query)
    if response:
        print("\nAgent Response:")
        print(response)

if __name__ == '__main__':
    main()
