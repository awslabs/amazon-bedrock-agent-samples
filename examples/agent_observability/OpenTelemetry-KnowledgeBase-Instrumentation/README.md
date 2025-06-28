# Amazon Bedrock Knowledge Base Observability with OpenTelemetry

This package provides OpenTelemetry instrumentation for Amazon Bedrock Knowledge Bases that sends trace data to any OpenTelemetry-compatible observability platform. It creates a complete observability solution for Bedrock KB operations, supporting both `retrieve` and `retrieveAndGenerate` operations.

## Overview

OpenTelemetry integration enables tracing, monitoring, and analyzing the performance and behavior of your Bedrock Knowledge Base operations. This observability solution helps in understanding KB interactions, debugging issues, and optimizing retrieval performance. It provides detailed metrics on retrieval results, document scores, and generation quality.

As the field of AI observability is still maturing, this implementation adheres to OpenTelemetry semantics as much as possible and will evolve as industry standards become more established.

## Features

- Comprehensive tracing for Knowledge Base retrieve and retrieveAndGenerate operations
- Result scoring and content metrics tracking for each retrieved document
- Document source and metadata attribution
- Generation quality metrics for retrieveAndGenerate operations
- Standardized attribute naming following OpenTelemetry conventions
- Compatible with any OpenTelemetry-compatible observability platform (e.g., Langfuse, Grafana, Datadog)
- Support for both cloud-hosted and self-hosted options
- Detailed trace and performance metrics for all KB operations

## Setup

### Prerequisites
1. AWS account with appropriate IAM permissions for Amazon Bedrock Knowledge Bases
2. An existing Amazon Bedrock Knowledge Base (or follow AWS documentation to create one)
3. An OpenTelemetry-compatible observability platform (examples include Langfuse, Grafana, Jaeger, etc.)

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
1. Add the following information in `config.json`
2. Fill in your OpenTelemetry endpoint credentials, knowledge base details, and other settings

```json
{
    "langfuse": {
        "project_name": "Your Project",
        "environment": "development",
        "langfuse_public_key": "your-public-key",
        "langfuse_secret_key": "your-secret-key",
        "langfuse_api_url": "your-otel-endpoint"
    },
    "kb": {
        "kbId": "your-knowledge-base-id"
    },
    "user": {
        "userId": "user123"
    },
    "question": {
        "question": "Your query to the knowledge base"
    }
}
```

## Quick Start
Run the main script to test both retrieve and retrieveAndGenerate operations:

```bash
python main.py
```

Or use the integration in your own code:

```python
from core import instrument_kb_operation, flush_telemetry
from core.configuration import create_tracer_provider
from opentelemetry.trace import get_tracer_provider
from opentelemetry.sdk.trace import TracerProvider

# Initialize the tracer provider first
if not isinstance(get_tracer_provider(), TracerProvider):
    create_tracer_provider(
        service_name="Your Project",
        environment="development"
    )

@instrument_kb_operation
def retrieve_from_kb(kbId: str, query: str, **kwargs):
    bedrock_kb_client = boto3.client("bedrock-agent-runtime")
    
    retrieve_params = {
        "knowledgeBaseId": kbId,
        "retrievalQuery": {
            "text": query
        },
        "retrievalConfiguration": {
            "vectorSearchConfiguration": {
                "numberOfResults": 3
            }
        }
    }

    response = bedrock_kb_client.retrieve(**retrieve_params)
    return response

@instrument_kb_operation
def retrieve_and_generate_from_kb(query: str, kbId: str, model_arn: str, **kwargs):
    bedrock_kb_client = boto3.client("bedrock-agent-runtime")
    
    response = bedrock_kb_client.retrieve_and_generate(
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

# Example usage
response = retrieve_from_kb(
    kbId="your-knowledge-base-id",
    query="your-query",
    operation_type="retrieve",
    userId="user-123",
    tags=["bedrock-kb", "example", "development"],
    trace_id=str(uuid.uuid4())
)

# Always flush telemetry before exiting
flush_telemetry()
```

## Deployment Options

### Cloud-Hosted Observability Platforms
Configure the integration using the cloud endpoint of your preferred OpenTelemetry-compatible observability platform, such as Langfuse Cloud.

### Self-Hosted Option
1. Deploy an OpenTelemetry collector or a compatible observability platform (like Langfuse, Jaeger, etc.) using Docker containers
2. Configure the integration using your self-hosted endpoint
3. Ideal for keeping all data within your AWS environment

## Trace Data Captured

The integration captures detailed metrics for Knowledge Base operations:

### For retrieve operations:
- Query text and operation parameters
- Number of retrieval results
- Individual and total retrieval scores
- Document content and metadata
- Source locations for retrieved documents
- Document content length
- HTTP status codes and error states

### For retrieveAndGenerate operations:
- Query text and model parameters
- Generated text content and length
- Citations and their relevance scores
- Retrieved references and their sources
- Total score across all retrieved documents
- HTTP status codes and error handling

## Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `langfuse_public_key` | API key for OTEL endpoint | Environment variable |
| `langfuse_secret_key` | Secret key for OTEL endpoint | Environment variable |
| `langfuse_api_url` | OTEL API endpoint URL | https://cloud.langfuse.com/api/public/otel |
| `project_name` | Project name | Amazon Bedrock KB |
| `environment` | Environment name | development |
| `userId` | User ID for tracking | anonymous |
| `tags` | Tags for filtering | [] |
| `operation_type` | Type of KB operation | retrieve |
| `trace_id` | Custom trace ID | UUID |

## Attribute Naming

This integration follows OpenTelemetry attribute naming conventions:

- `operation.name` - Name of the operation (KB_retrieve or KB_retrieveandgenerate)
- `input.query` - Search query text
- `retrieval.document_count` - Number of documents retrieved
- `result.[index].score` - Relevance score for each document
- `result.[index].source` - Source location for each document
- `result.[index].content_text` - Text content for each document
- `result.[index].content_length` - Content length for each document
- `generated_content.text` - Generated text for retrieveAndGenerate operations
- `generated_content.length` - Length of generated content
- `total_score` - Total relevance score across all documents
- `http.status_code` - HTTP response status code

## Notebook Integration

A Jupyter notebook (`bedrock-kb-langfuse-integration.ipynb`) is also provided to help you get started and visualize the integration in action. The notebook includes:

- Step-by-step setup of OpenTelemetry with Langfuse
- Examples of both retrieve and retrieveAndGenerate operations
- Visualization of the retrieval results
- Troubleshooting and validation steps
