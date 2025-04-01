"""Configuration for OpenTelemetry with Langfuse."""

import base64
import logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from openinference.semconv.resource import ResourceAttributes
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.sdk.resources import Resource

from .settings_management import ObservabilityConfig

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def create_tracer_provider(config: ObservabilityConfig, timeout: int = 300):
    """Create an OpenTelemetry TracerProvider configured for Langfuse."""

    # Create resource attributes
    resource = Resource.create(
        {
            ResourceAttributes.PROJECT_NAME: config.PROJECT_NAME,
            "service.name": config.PROJECT_NAME,
            "deployment.environment": config.ENVIRONMENT,
        }
    )

    # Create tracer provider with resource
    tracer_provider = TracerProvider(resource=resource)

    if config.API_URL and config.PRODUCE_BEDROCK_OTEL_TRACES:
        endpoint = f"{config.API_URL}/v1/traces"

        # Configure Langfuse exporter if credentials are provided
        if config.LANGFUSE_PUBLIC_KEY and config.LANGFUSE_SECRET_KEY:

            # Generate Basic auth header for Langfuse
            langfuse_auth = base64.b64encode(
                f"{config.LANGFUSE_PUBLIC_KEY}:{config.LANGFUSE_SECRET_KEY}".encode()
            ).decode()
            # Configure OTLP exporter for Langfuse - match the original implementation
            logger.info(f"Using Langfuse endpoint: {endpoint}")

            langfuse_exporter = OTLPSpanExporter(
                endpoint=endpoint,
                headers={"Authorization": f"Basic {langfuse_auth}"},
                timeout=timeout,
            )

            # Add Langfuse exporter to tracer provider
            # Use default settings for simplicity
            logger.info(
                f"Langfuse exporter configured for project: {config.PROJECT_NAME}"
            )
            tracer_provider.add_span_processor(BatchSpanProcessor(langfuse_exporter))
        else:
            span_exporter = OTLPSpanExporter(
                endpoint=endpoint,
                timeout=timeout,
            )
            tracer_provider.add_span_processor(
                BatchSpanProcessor(span_exporter=span_exporter)
            )

    else:
        # tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        logger.warning(
            "Credentials not provided, telemetry will not be created or exported"
        )

    # Set as global tracer provider
    trace.set_tracer_provider(tracer_provider)
