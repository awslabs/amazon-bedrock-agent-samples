import boto3
import uuid
import os

from opentelemetry import trace, metrics
from opentelemetry.trace import SpanKind
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from observability import observe_response
from observability.attributes import SpanAttributes


def read_secret(secret: str):
    try:
        with open(f"/etc/secrets/{secret}", "r") as f:
            return f.read().rstrip()
    except Exception:
        return os.environ.get(secret.replace("-", "_").upper(), "")


resource = Resource.create(
    {"service.name": "bedrock-agent", "service.version": "0.0.0"}
)
token = os.environ["DT_TOKEN"]
otlp_endpoint = os.environ["OTLP_ENDPOINT"]
headers = {"Authorization": f"Api-Token {token}"}

# OpenTelemetry Span configuration
exporter = OTLPSpanExporter(
    endpoint=f"{otlp_endpoint}/v1/traces",
    headers=headers,
)
provider = TracerProvider(resource=resource)
provider.add_span_processor(SimpleSpanProcessor(exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("bedrock-agents")

if __name__ == "__main__":
    key = read_secret("aws-key")
    sec = read_secret("aws-secret")

    client = boto3.client(
        "bedrock-agent-runtime",
        region_name="eu-central-1",
        aws_access_key_id=key,
        aws_secret_access_key=sec,
    )
    agent_prompt = "Good evening. What can I do in new york?"
    agent_id = os.environ["AGENT_ID"]  # "IJXAKWPIGC"
    agent_alias_id = os.environ["AGENT_ALIAS_ID"]  # "GS1AVWVJEP"
    session_id = str(uuid.uuid4())
    with tracer.start_as_current_span(
        name=f"invoke_agent {agent_id}",
        kind=SpanKind.CLIENT,
        attributes={
            SpanAttributes.OPERATION_NAME: "invoke_agent",
            SpanAttributes.SYSTEM: "aws.bedrock",
            SpanAttributes.AGENT_ID: agent_id,
        },
    ) as rootSpan:
        response = client.invoke_agent(
            inputText=agent_prompt,
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            enableTrace=True,
            streamingConfigurations={
                "streamFinalResponse": True,
                "applyGuardrailInterval": 10,
            },
        )
        output = observe_response(response)
        print(output)

    provider.shutdown()
