import boto3
import uuid
import os
import logging

from opentelemetry import trace, metrics
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (OTLPLogExporter)
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.trace import SpanKind
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from observability import observe_response
from observability.attributes import SpanAttributes
from metrics import (init_metrics)

# Set service name
service_name = os.environ["OTEL_SERVICE_NAME"]

resource = Resource.create(
    {"service.name": "bedrock-agent", "service.version": "0.0.0"}
)
token = os.environ["OTEL_EXPORTER_OTLP_HEADERS"]
otlp_endpoint = os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"]
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
    # Connect AWS Bedrock
    client = boto3.client(
        "bedrock-agent-runtime",
        region_name="us-east-1",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
    )
    agent_prompt = os.environ["AGENT_PROMPT"]
    agent_id = os.environ["AGENT_ID"]
    agent_alias_id = os.environ["AGENT_ALIAS_ID"]
    session_id = str(uuid.uuid4())

    # Initialize Traces and Metrics
    tracer = trace.get_tracer_provider().get_tracer(service_name)
    meter = metrics.get_meter_provider().get_meter(service_name)
    rec_svc_metrics = init_metrics(meter)

    # OpenTelemetry Initialize Logs
    logger_provider = LoggerProvider(
        resource=Resource.create(
            {
                'service.name': service_name,
            }
        ),
    )
    set_logger_provider(logger_provider)
    log_exporter = OTLPLogExporter(insecure=True)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)

    # Attach OTLP handler to logger
    logger = logging.getLogger('main')
    logger.addHandler(handler)

    trace.get_current_span().set_attribute("Session Id", session_id)
    trace.get_current_span().set_attribute("Prompt", agent_prompt)

    with tracer.start_as_current_span(
        name=f"invoke_agent {agent_id}",
        kind=SpanKind.CLIENT,
        attributes={
            SpanAttributes.OPERATION_NAME: "invoke_agent",
            SpanAttributes.SYSTEM: "aws.bedrock",
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

    provider.shutdown()
