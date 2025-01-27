import boto3
import json
import time
import os

sts_client = boto3.client("sts")
iam_client = boto3.client("iam")
session = boto3.session.Session()
region = session.region_name
account_id = sts_client.get_caller_identity()["Account"]

lambda_function_arn = os.environ["LAMBDA_FUNCTION_ARN"]
lambda_function_name = os.environ["LAMBDA_FUNCTION_NAME"]
agent_name = "video-games-sales-assistant"
agent_bedrock_allow_policy_name = f"{agent_name}-{region}-policy"
agent_role_name = f"AmazonBedrockRoleForAgents_{agent_name}_{region}"
agent_foundation_model = "anthropic.claude-3-5-haiku-20241022-v1:0"
if region == "us-east-1":
    agent_foundation_model = f"arn:aws:bedrock:us-east-1:{account_id}:inference-profile/us.anthropic.claude-3-5-haiku-20241022-v1:0"

print(agent_foundation_model)

# Create a Bedrock Agent client

bedrock_agent_client = boto3.client("bedrock-agent")

# Read files

with open("resources/agent-instructions.txt", "r") as file:
    agent_instructions = file.read()

with open("resources/agent-orchestration-strategy.txt", "r") as file:
    agent_orchestration_strategy = file.read()

with open("resources/agent-api-schema.json", "r") as file:
    agent_api_schema = file.read()

# Create IAM policies for agent

bedrock_agent_bedrock_allow_policy_statement = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AmazonBedrockAgentInferenceProfilesCrossRegionPolicyProd",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:GetInferenceProfile",
                "bedrock:GetFoundationModel",
            ],
            "Resource": [
                f"arn:aws:bedrock:us-east-1:{account_id}:inference-profile/us.anthropic.claude-3-5-haiku-20241022-v1:0",
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-haiku-20241022-v1:0",
            ],
        }
    ],
}

bedrock_policy_json = json.dumps(bedrock_agent_bedrock_allow_policy_statement)

agent_bedrock_policy = iam_client.create_policy(
    PolicyName=agent_bedrock_allow_policy_name, PolicyDocument=bedrock_policy_json
)

# Create IAM Role for the agent and attach IAM policies

assume_role_policy_document = assume_role_policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AmazonBedrockAgentBedrockFoundationModelPolicyProd",
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }
    ],
}

assume_role_policy_document_json = json.dumps(assume_role_policy_document)
agent_role = iam_client.create_role(
    RoleName=agent_role_name, AssumeRolePolicyDocument=assume_role_policy_document_json
)

# Pause to make sure role is created

time.sleep(10)

iam_client.attach_role_policy(
    RoleName=agent_role_name, PolicyArn=agent_bedrock_policy["Policy"]["Arn"]
)

time.sleep(10)

# Create the Bedrock agent

create_agent_response = bedrock_agent_client.create_agent(
    foundationModel=agent_foundation_model,
    agentName=agent_name,
    orchestrationType="DEFAULT",
    promptOverrideConfiguration={
        "promptConfigurations": [
            {
                "basePromptTemplate": agent_orchestration_strategy,
                "inferenceConfiguration": {
                    "maximumLength": 2048,
                    "stopSequences": ["</invoke>", "</answer>", "</error>"],
                    "temperature": 0.0,
                    "topK": 250,
                    "topP": 1.0,
                },
                "parserMode": "DEFAULT",
                "promptCreationMode": "OVERRIDDEN",
                "promptState": "ENABLED",
                "promptType": "ORCHESTRATION",
            },
        ]
    },
    instruction=agent_instructions,
    agentResourceRoleArn=agent_role["Role"]["Arn"],
)

agent_id = create_agent_response["agent"]["agentId"]
agent_arn = create_agent_response["agent"]["agentArn"]

time.sleep(10)

create_action_group_response = bedrock_agent_client.create_agent_action_group(
    agentId=agent_id,
    actionGroupName="executesqlquery",
    agentVersion="DRAFT",
    actionGroupExecutor={"lambda": lambda_function_arn},
    apiSchema={"payload": agent_api_schema},
    description="An action group to execute SQL queries",
)

# Add Lambda permission

lambda_client = boto3.client("lambda")

response = lambda_client.add_permission(
    FunctionName=lambda_function_name,
    StatementId="agent",
    Action="lambda:InvokeFunction",
    Principal="bedrock.amazonaws.com",
    SourceArn=agent_arn,
)

# Print the agent Id and ARN
print("-----------------------------------------")
print(f"Agent Id: {agent_id}")
print(f"Agent ARN: {agent_arn}")
print(
    f"Action Group Id: {create_action_group_response['agentActionGroup']['actionGroupId']}"
)
