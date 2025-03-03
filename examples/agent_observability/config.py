import base64
import logging
import os
from phoenix.otel import register

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment settings
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

# Project configuration
def get_project_name():
    """Get project name from environment, allowing for dynamic updates"""
    return os.environ.get("PROJECT_NAME", "BA Latency Testing VA")

# Langfuse configuration
LANGFUSE_OTEL_API = "https://us.cloud.langfuse.com/api/public/otel"  # US Data Region
LANGFUSE_PUBLIC_KEY = "langfuse-public-key"
LANGFUSE_SECRET_KEY = "langfuse-secret-key"
LANGFUSE_AUTH = base64.b64encode(f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()).decode()

# Arize Cloud configuration
ARIZE_CLOUD_API_KEY = "arize-cloud-key"
ARIZE_CLOUD_ENDPOINT = "https://app.phoenix.arize.com/v1/traces"

# Arize Local configuration
ARIZE_LOCAL_ENDPOINT = "local-host-end-point" # example http://localhost:6006/v1/traces

def configure_arize_cloud():
    """Configure environment for Arize Cloud"""
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"api_key={ARIZE_CLOUD_API_KEY}"
    os.environ["PHOENIX_CLIENT_HEADERS"] = f"api_key={ARIZE_CLOUD_API_KEY}"
    os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "https://app.phoenix.arize.com"
    
    return register(
        project_name=get_project_name(),
        endpoint=ARIZE_CLOUD_ENDPOINT
    )

def configure_arize_local():
    """Configure for Arize Local"""
    return register(
        project_name=get_project_name(),
        endpoint=ARIZE_LOCAL_ENDPOINT,
        batch=True,
        protocol="http/protobuf"
    )

def configure_langfuse():
    """Configure for Langfuse"""
    endpoint_url = f"{LANGFUSE_OTEL_API}/v1/traces"
    return register(
        project_name=get_project_name(),
        endpoint=endpoint_url,
        batch=True,
        protocol="http/protobuf",
        headers={"Authorization": f"Basic {LANGFUSE_AUTH}"}
    )

def create_tracer_provider(provider=None):
    """Create and configure the tracer provider based on selected provider
    
    Args:
        provider (str, optional): The provider to use. 
            Options: "langfuse", "arize_local", "arize_cloud"
            If None, defaults to "arize_cloud"
    
    Returns:
        The configured tracer provider
    """
    # Default to arize_cloud if no provider specified
    if provider is None:
        provider = "arize_cloud"
    
    if provider == "langfuse":
        logger.info("Using Langfuse for tracing")
        tracer_provider = configure_langfuse()
    elif provider == "arize_local":
        logger.info("Using Arize Local for tracing")
        tracer_provider = configure_arize_local()
    elif provider == "arize_cloud":
        logger.info("Using Arize Cloud for tracing")
        tracer_provider = configure_arize_cloud()
    else:
        logger.warning(f"Unknown provider: {provider}, defaulting to Arize Cloud")
        tracer_provider = configure_arize_cloud()
    
    return tracer_provider