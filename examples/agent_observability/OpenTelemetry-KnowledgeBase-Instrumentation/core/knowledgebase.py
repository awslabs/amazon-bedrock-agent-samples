import json
import uuid
import logging
from functools import wraps
from typing import Dict, Any

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from .configuration import create_tracer_provider

from .tracing import flush_telemetry as flush_telemetry_core
from .constants import KBOperationTypes

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize OpenTelemetry global tracer
create_tracer_provider()
tracer = trace.get_tracer("bedrock-kb-tracing")

def json_safe(obj):
    """Convert object to JSON-safe format, handling complex types."""
    if isinstance(obj, dict):
        return json.dumps(obj)
    return obj

def instrument_kb_operation(func):
    """
    Decorator to instrument Bedrock Knowledge Base operations with OpenTelemetry.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        operation_type = kwargs.pop("operation_type", "unknown")
        trace_id = kwargs.pop("trace_id", str(uuid.uuid4()))
        user_id = kwargs.pop("userId", "anonymous")
        tags = kwargs.pop("tags", [])
        query = kwargs.get("query", "")

        with tracer.start_as_current_span(
            name=f"KB_Operation: {operation_type}",
            kind=SpanKind.CLIENT,
            attributes={
                "operation.name": f"KB_{operation_type}",
                "user.id": user_id,
                "trace.id": trace_id,
                "tags": json_safe(tags),
                "input.query": query,
            },
        ) as span:
            try:
                # Call the function and get the response
                response = func(*args, **kwargs)

                # Handling for the response based on the operation type
                if operation_type == "retrieve":
                    # Handling for 'retrieve' operation
                    retrieval_results = response.get('retrievalResults', [])
                    request_id = response.get('ResponseMetadata', {}).get('RequestId', 'unknown')
                    status_code = response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0)

                    span.set_attribute("http.status_code", status_code)
                    span.set_attribute("trace.id", request_id)
                    span.set_attribute("retrieval.document_count", len(retrieval_results))

                    total_score = 0
                    for index, result in enumerate(retrieval_results):
                        content = result.get('content', {}).get('text', '')
                        score = result.get('score', 0)
                        total_score += score
                        source = result.get('location', {}).get('s3Location', {}).get('uri', '')

                        span.set_attribute(f"result.{index}.score", score)
                        span.set_attribute(f"result.{index}.source", source)
                        span.set_attribute(f"result.{index}.content_text", content)
                        span.set_attribute(f"result.{index}.content_length", len(content))

                    span.set_attribute("total_score", total_score)

                elif operation_type == "retrieveandgenerate":
                    # Handling for 'retrieveandgenerate' operation
                    if isinstance(response, str):
                        # If the response is a string, this is from the `retrieve_and_generate` call
                        generated_content = response
                        status_code = 200  # Assuming a successful operation for generated text
                        span.set_attribute("http.status_code", status_code)
                        span.set_attribute("generated_content.text", generated_content)
                        span.set_attribute("generated_content.length", len(generated_content))

                    else:
                        # Handle the normal dictionary response
                        citations = response.get('citations', [])
                        generated_content = response.get('output', {}).get('text', '')
                        request_id = response.get('ResponseMetadata', {}).get('RequestId', 'unknown')
                        status_code = response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0)

                        span.set_attribute("http.status_code", status_code)
                        span.set_attribute("trace.id", request_id)
                        span.set_attribute("citations.count", len(citations))
                        span.set_attribute("generated_content.text", generated_content)
                        span.set_attribute("generated_content.length", len(generated_content))

                        total_score = 0
                        for citation_index, citation in enumerate(citations):
                            generated_text = citation.get('generatedResponsePart', {}).get('textResponsePart', {}).get('text', '')
                            retrieved_references = citation.get('retrievedReferences', [])

                            # Track the generated content from citations
                            span.set_attribute(f"citation.{citation_index}.generated_text", generated_text)

                            # Process each retrieved reference
                            for ref_index, ref in enumerate(retrieved_references):
                                content = ref.get('content', {}).get('text', '')
                                score = ref.get('score', 0)
                                total_score += score
                                source = ref.get('location', {}).get('s3Location', {}).get('uri', '')

                                # Set attributes for each reference
                                span.set_attribute(f"citation.{citation_index}.retrieved_reference.{ref_index}.score", score)
                                span.set_attribute(f"citation.{citation_index}.retrieved_reference.{ref_index}.source", source)
                                span.set_attribute(f"citation.{citation_index}.retrieved_reference.{ref_index}.content_text", content)
                                span.set_attribute(f"citation.{citation_index}.retrieved_reference.{ref_index}.content_length", len(content))

                        span.set_attribute("total_score", total_score)

                # Set status based on HTTP status code
                if status_code == 200:
                    span.set_status(Status(StatusCode.OK))
                else:
                    span.set_status(Status(StatusCode.ERROR))
                    span.set_attribute("error.message", f"KB {operation_type} failed with status code {status_code}")

                return response
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error(f"Error during KB operation: {str(e)}", exc_info=True)
                raise

    return wrapper


def flush_telemetry():
    """Force flush OpenTelemetry data to ensure exports complete."""
    flush_telemetry_core()
