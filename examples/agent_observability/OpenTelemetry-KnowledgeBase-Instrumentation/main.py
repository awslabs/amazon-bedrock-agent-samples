import os
import json
import uuid
import base64
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration from the config file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Set environment variables for OpenTelemetry
os.environ["OTEL_SERVICE_NAME"] = 'Langfuse'
os.environ["DEPLOYMENT_ENVIRONMENT"] = config["langfuse"]["environment"]
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{config['langfuse']['langfuse_api_url']}api/public/otel/v1/traces"
auth_token = base64.b64encode(
    f"{config['langfuse']['langfuse_public_key']}:{config['langfuse']['langfuse_secret_key']}".encode()
).decode()
os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {auth_token}"

import boto3
from core.timer_lib import timer
from core import instrument_kb_operation, flush_telemetry
from core.configuration import create_tracer_provider

from opentelemetry.trace import get_tracer_provider
from opentelemetry.sdk.trace import TracerProvider

# Initialize OpenTelemetry tracer
if not isinstance(get_tracer_provider(), TracerProvider):
    create_tracer_provider(
        service_name=config["langfuse"]["project_name"],
        environment=config["langfuse"]["environment"]
    )

print("✅ Tracer provider initialized with Langfuse endpoint.")

bedrock_agent_runtime = boto3.client("bedrock-agent-runtime")

@instrument_kb_operation
def retrieve_from_kb(kbId: str, query: str, **kwargs):
    """
    Retrieves documents from the knowledge base.
    """
    retrieve_params = {
        "knowledgeBaseId": kbId,
        "retrievalQuery": {"text": query},
        "retrievalConfiguration": {"vectorSearchConfiguration": {"numberOfResults": 3}},
    }

    response = bedrock_agent_runtime.retrieve(**retrieve_params)
    return response

@instrument_kb_operation
def retrieve_and_generate_from_kb(query: str, kbId: str, model_arn: str, **kwargs):
    """
    Retrieves documents and generates a response based on the retrieved information.
    """
    response = bedrock_agent_runtime.retrieve_and_generate(
        input={
            'text': query
        },
        retrieveAndGenerateConfiguration={
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': kbId,
                'modelArn': model_arn
            },
            'type': 'KNOWLEDGE_BASE'
        }
    )
    return response


if __name__ == "__main__":
    trace_id = str(uuid.uuid4())
    tags = ["bedrock-kb", "example", "development"]
    query = config["question"]["question"]
    model_arn = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"

    # Call the retrieve operation
    print("\n🔍 Performing KB Retrieve Operation:")
    retrieve_response = retrieve_from_kb(
        kbId=config["kb"]["kbId"],
        query=query,
        operation_type="retrieve",
        userId=config["user"]["userId"],
        tags=tags,
        trace_id=trace_id,
        project_name=config["langfuse"]["project_name"],
        environment=config["langfuse"]["environment"],
        langfuse_public_key=config["langfuse"]["langfuse_public_key"],
        langfuse_secret_key=config["langfuse"]["langfuse_secret_key"],
        langfuse_api_url=config["langfuse"]["langfuse_api_url"]
    )

    # Print retrieve results
    if isinstance(retrieve_response, dict) and "error" in retrieve_response:
        print(f"\nError: {retrieve_response['error']}")
    else:
        print("\n🔍 KB Retrieve Results:")
        for idx, result in enumerate(retrieve_response.get('retrievalResults', []), 1):
            print(f"\nResult {idx}:")
            print(f"Score: {result.get('score', 'N/A')}")
            print(f"Content: {result.get('content', {}).get('text', 'N/A')[:100]}...")
            print(f"Source: {result.get('location', {}).get('s3Location', {}).get('uri', 'N/A')}")

    # Call the retrieve and generate operation
    print("\n🔍 Performing KB Retrieve and Generate Operation:")
    generated_text = retrieve_and_generate_from_kb(
        query=query,
        kbId=config["kb"]["kbId"],
        model_arn=model_arn,
        operation_type="retrieveandgenerate",
        userId=config["user"]["userId"],
        tags=tags,
        trace_id=trace_id,
        project_name=config["langfuse"]["project_name"],
        environment=config["langfuse"]["environment"],
        langfuse_public_key=config["langfuse"]["langfuse_public_key"],
        langfuse_secret_key=config["langfuse"]["langfuse_secret_key"],
        langfuse_api_url=config["langfuse"]["langfuse_api_url"]
    )

    # Print retrieve and generate results
    print(f"\nGenerated Text 2: {generated_text['output']['text']}")
    
    # Flush telemetry
    flush_telemetry()
