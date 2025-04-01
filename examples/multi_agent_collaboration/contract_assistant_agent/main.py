#!/usr/bin/env python

import sys
from pathlib import Path
import time
import os
import argparse
import boto3
from textwrap import dedent
import logging
import uuid
from typing import Optional
from botocore.exceptions import ClientError

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.utils.bedrock_agent import Agent, SupervisorAgent, agents_helper
from src.utils.knowledge_base_helper import KnowledgeBasesForAmazonBedrock

# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

kb_helper = KnowledgeBasesForAmazonBedrock()
s3_client = boto3.client("s3")
sts_client = boto3.client("sts")

logging.basicConfig(
    format="[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def upload_directory(path, bucket_name):
    for root, dirs, files in os.walk(path):
        for file in files:
            file_to_upload = os.path.join(root, file)
            dest_key = f"{path}/{file}"
            print(f"uploading file {file_to_upload} to {bucket_name}")
            s3_client.upload_file(file_to_upload, bucket_name, dest_key)


def update_lambda_configuration(function_name: str, bucket_name: str) -> bool:
    """
    Update Lambda function with S3 and Bedrock permissions and environment variables.

    Args:
        function_name (str): Name of the Lambda function
        bucket_name (str): Name of the S3 bucket to add as environment variable

    Returns:
        bool: True if successful, False if any step fails
    """
    # Initialize AWS clients
    lambda_client = boto3.client("lambda")
    iam = boto3.client("iam")

    try:
        # Get the role name from Lambda function
        lambda_config = lambda_client.get_function_configuration(
            FunctionName=function_name
        )
        role_arn = lambda_config["Role"]
        role_name = role_arn.split("/")[-1]
        print(f"Found role name: {role_name}")

        # AWS managed policies to attach
        managed_policies = [
            "arn:aws:iam::aws:policy/AmazonS3FullAccess",
            "arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
        ]

        # Attach managed policies
        for policy_arn in managed_policies:
            try:
                iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
                print(f"Successfully attached {policy_arn} to role {role_name}")
            except ClientError as e:
                if e.response["Error"]["Code"] == "EntityAlreadyExists":
                    print(f"Policy {policy_arn} is already attached to the role")
                else:
                    print(f"Error attaching {policy_arn}: {str(e)}")

        # Update environment variables
        current_env = lambda_config.get("Environment", {}).get("Variables", {})
        current_env.update({"BUCKET_NAME": bucket_name})

        lambda_client.update_function_configuration(
            FunctionName=function_name, Environment={"Variables": current_env}
        )
        print(f"Successfully added environment variable BUCKET_NAME={bucket_name}")

        # Verify changes
        print("\nVerifying changes...")

        # Verify Lambda configuration
        updated_config = lambda_client.get_function_configuration(
            FunctionName=function_name
        )
        print("\nLambda Environment Variables:")
        print(updated_config.get("Environment", {}).get("Variables", {}))

        # Verify attached policies
        attached_policies = iam.list_attached_role_policies(RoleName=role_name)
        print("\nAttached Policies:")
        for policy in attached_policies["AttachedPolicies"]:
            print(f"- {policy['PolicyName']}")

        return True

    except ClientError as e:
        print(f"AWS Error: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False


def attach_layer(function_name: str, layer_name: str, zip_file_path: str) -> bool:
    """
    Upload a layer from existing zip file and attach it to the Lambda function.

    Args:
        function_name (str): Name of the Lambda function
        layer_name (str): Name for the new layer
        zip_file_path (str): Path to the existing zip file

    Returns:
        bool: True if successful, False otherwise
    """
    lambda_client = boto3.client("lambda")

    try:
        # Upload layer from existing zip
        with open(zip_file_path, "rb") as zip_file:
            response = lambda_client.publish_layer_version(
                LayerName=layer_name,
                Description=f"Layer for {function_name}",
                Content={"ZipFile": zip_file.read()},
                CompatibleRuntimes=["python3.12"],
            )

        layer_version_arn = response["LayerVersionArn"]
        print(f"Created layer: {layer_version_arn}")

        # Attach layer to function
        lambda_config = lambda_client.get_function_configuration(
            FunctionName=function_name
        )

        # Get existing layers
        existing_layers = lambda_config.get("Layers", [])
        layer_arns = [layer["Arn"] for layer in existing_layers]

        # Add new layer
        layer_arns.append(layer_version_arn)

        # Update function configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name, Layers=layer_arns
        )
        print(f"Attached layer to {function_name}")

        # Verify the update
        updated_config = lambda_client.get_function_configuration(
            FunctionName=function_name
        )
        print("\nCurrent Layers:")
        for layer in updated_config.get("Layers", []):
            print(f"- {layer['Arn']}")

        return True

    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def delete_lambda_function(function_name):
    """
    Delete a Lambda function by its name

    Args:
        function_name (str): Name of the Lambda function to delete

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        # Create Lambda client
        lambda_client = boto3.client("lambda")

        # Delete the function
        response = lambda_client.delete_function(FunctionName=function_name)

        print(f"Successfully deleted Lambda function: {function_name}")
        return True

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"Function {function_name} does not exist")
        else:
            print(f"Error deleting function {function_name}: {str(e)}")
        return False

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False


def main(args):
    if args.clean_up == "true":
        Agent.set_force_recreate_default(True)
        agents_helper.delete_agent("contracts_assistant", verbose=True)
        agents_helper.delete_agent("general_contract_assistant", verbose=True)
        agents_helper.delete_agent("existing_contract_assistant", verbose=True)
        agents_helper.delete_agent("contract_drafting_agent", verbose=True)
        kb_helper.delete_kb("contract-templates-kb", delete_s3_bucket=True)
        delete_lambda_function("existing_contract_assistant_ag")
        delete_lambda_function("contract_drafting_agent_ag")
        return

    if args.recreate_agents == "false":
        Agent.set_force_recreate_default(False)
    else:
        Agent.set_force_recreate_default(True)
        agents_helper.delete_agent("contracts_assistant", verbose=True)

    bucket_name = None

    print("creating contract templates KB")
    kb_name = "contract-templates-kb"
    kb_id, ds_id = kb_helper.create_or_retrieve_knowledge_base(
        kb_name,
        kb_description="Knowledge base containing contract templates and guidelines for drafting different types of contracts.",
        data_bucket_name=bucket_name,
    )
    print(f"KB name: {kb_name}, kb_id: {kb_id}, ds_id: {ds_id}\n")
    bucket_name = kb_helper.get_data_bucket_name()

    if args.recreate_agents == "true":
        print("uploading contract templates")
        upload_directory("contract_templates", f"{bucket_name}")
        time.sleep(30)
        kb_helper.synchronize_data(kb_id, ds_id)
        print("KB sync completed\n")

    general_contract_assistant = Agent.create(
        name="general_contract_assistant",
        role="General contract Questions Assistant",
        goal="Handle conversations about general contract or legal questions, like based on the requirement determine appropriate contract type",
        instructions=dedent(
            """
            Use thos knowledge base to answer general questions about contract or agreement type."""
        ),
        kb_id=kb_id,
        llm="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    )

    existing_contract_assistant = Agent.create(
        name="existing_contract_assistant",
        role="Existing Contract Assistant",
        goal="Handle queries about existing contracts",
        instructions=dedent(
            """
            You handle queries about existing contracts, including retrieving contract status,
            details, and answering questions about existing agreements."""
        ),
        tool_code="existing_contract_function.py",
        tool_defs=[
            {
                "name": "get_contract_status",
                "description": "Retrieves status of an existing contract",
                "parameters": {
                    "contract_id": {
                        "description": "The unique identifier for the contract",
                        "type": "string",
                        "required": False,
                    }
                },
            },
            {
                "name": "get_contract_details",
                "description": "Retrieves detailed information about a contract",
                "parameters": {
                    "contract_id": {
                        "description": "The unique identifier for the contract",
                        "type": "string",
                        "required": False,
                    }
                },
            },
        ],
        llm="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    )

    contract_drafting_agent = Agent.create(
        name="contract_drafting_agent",
        role="Contract Drafting Agent",
        goal="Draft new contracts based on requirements",
        instructions=dedent(
            """
            You help draft new contracts by collecting required information, selecting appropriate
            templates, and generating contract drafts. You can handle purchase agreements,
            franchise agreements, and time and materials contracts."""
        ),
        tool_code="contract_drafting_function.py",
        tool_defs=[
            {
                "name": "determine_contract_type",
                "description": "Analyzes requirements to determine contract type",
                "parameters": {
                    "requirements": {
                        "description": "Description of contract requirements",
                        "type": "string",
                        "required": True,
                    }
                },
            },
            {
                "name": "draft_contract",
                "description": "Creates contract draft based on type and details",
                "parameters": {
                    "contract_type": {
                        "description": "Type of contract to draft",
                        "type": "string",
                        "required": True,
                    },
                    "contract_details": {
                        "description": "JSON string containing contract details",
                        "type": "string",
                        "required": True,
                    },
                },
            },
        ],
        llm="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    )

    contracts_assistant = SupervisorAgent.create(
        "contracts_assistant",
        role="Contracts Assistant",
        goal="Provide unified experience for contract-related queries",
        collaboration_type="SUPERVISOR_ROUTER",
        instructions=dedent(
            f"""
            Act as a helpful contracts assistant, managing conversations about:
            - general questions like determining appropriate contract types
            - Retrieving existing contract information
            - Drafting new contracts
            Use the {kb_name} knowledge base for contract templates and guidelines."""
        ),
        collaborator_agents=[
            {
                "agent": "general_contract_assistant",
                "instructions": "Use for general questions like determining appropriate contract type",
            },
            {
                "agent": "existing_contract_assistant",
                "instructions": "Use for existing contract queries",
            },
            {
                "agent": "contract_drafting_agent",
                "instructions": "Use for drafting new contracts",
            },
        ],
        collaborator_objects=[
            general_contract_assistant,
            existing_contract_assistant,
            contract_drafting_agent,
        ],
        llm="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        verbose=False,
    )
    # Update lambda function to provide access to s3 and bedrock
    function_name = "contract_drafting_agent_ag"
    print(f"Starting update for Lambda function role: {function_name}")
    success = update_lambda_configuration(function_name, bucket_name)
    if success:
        print("\nSuccessfully updated lambda IAM and env variable!")
    else:
        print(
            "\nFailed to update lambda IAM and env variable. Check the logs above for details."
        )
    layer_name = "contract_drafting_dependencies"
    zip_file_path = "docx-layer.zip"
    print(f"Creating and attaching layer for {function_name}")
    success = attach_layer(function_name, layer_name, zip_file_path)
    if success:
        print("\nSuccessfully created and attached layer!")
    else:
        print("\nFailed to create and attach layer. Check the logs above for details.")

    if args.recreate_agents == "false":
        print("\n\nInvoking supervisor agent...\n\n")
        session_id = str(uuid.uuid4())

        requests = [
            "I need a contract for purchasing equipments",
            "Can you show me the status of contract #12345?",
            "What are the key terms in my existing service agreement?",
            "I need to draft a franchise agreement for my restaurant chain",
            "Can you help me create a time and materials contract for consulting services?",
        ]

        for request in requests:
            print(f"\n\nRequest: {request}\n\n")
            result = contracts_assistant.invoke(
                request,
                session_id=session_id,
                enable_trace=True,
                trace_level=args.trace_level,
            )
            print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--recreate_agents",
        required=False,
        default=True,
        help="False if reusing existing agents.",
    )
    parser.add_argument(
        "--clean_up",
        required=False,
        default=False,
        help="True if cleaning up agents resources.",
    )
    parser.add_argument(
        "--trace_level",
        required=False,
        default="core",
        help="The level of trace, 'core', 'outline', 'all'.",
    )
    args = parser.parse_args()
    main(args)
