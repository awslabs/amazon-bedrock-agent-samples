import boto3
import os

sts_client = boto3.client("sts")
iam_client = boto3.client("iam")
session = boto3.session.Session()
region = session.region_name
account_id = sts_client.get_caller_identity()["Account"]

agent_id = os.environ["AGENT_ID"]
agent_arn = os.environ["AGENT_ARN"]
action_group_id = os.environ["ACTION_GROUP_ID"]
lambda_function_arn = os.environ["LAMBDA_FUNCTION_ARN"]
lambda_function_name = os.environ["LAMBDA_FUNCTION_NAME"]

agent_name = "video-games-sales-assistant"
agent_bedrock_allow_policy_name = f"{agent_name}-{region}-policy"
agent_role_name = f"AmazonBedrockRoleForAgents_{agent_name}_{region}"


# Read files
with open("resources/agent-api-schema.json", "r") as file:
    agent_api_schema = file.read()

# Create a Bedrock Agent client

bedrock_agent_client = boto3.client("bedrock-agent")

# Delete Amazon Bedrock Agent

create_action_group_response = bedrock_agent_client.update_agent_action_group(
    agentId=agent_id,
    actionGroupId=action_group_id,
    actionGroupName="executesqlquery",
    agentVersion="DRAFT",
    actionGroupExecutor={"lambda": lambda_function_arn},
    apiSchema={"payload": agent_api_schema},
    actionGroupState="DISABLED",
)

action_group_deletion = bedrock_agent_client.delete_agent_action_group(
    agentId=agent_id, agentVersion="DRAFT", actionGroupId=action_group_id
)

agent_deletion = bedrock_agent_client.delete_agent(agentId=agent_id)

# Remove IAM role and policies for agent

am_client = boto3.client("iam")

iam_client.detach_role_policy(
    RoleName=agent_role_name,
    PolicyArn=f"arn:aws:iam::{account_id}:policy/{agent_bedrock_allow_policy_name}",
)
iam_client.delete_role(RoleName=agent_role_name)
iam_client.delete_policy(
    PolicyArn=f"arn:aws:iam::{account_id}:policy/{agent_bedrock_allow_policy_name}"
)

# Remove Lambda permission

lambda_client = boto3.client("lambda")

response = lambda_client.remove_permission(
    FunctionName=lambda_function_name, StatementId="agent"
)
