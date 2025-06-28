"""Constants for the Bedrock Knowledge Base Langfuse integration"""

class SpanAttributes:
    """OpenTelemetry semantic conventions for KB operations"""
    # KB attributes
    KB_SYSTEM = "gen_ai.system"
    KB_QUERY = "kb.query"
    KB_RESULTS = "kb.results"
    KB_USAGE_TOTAL_TOKENS = "kb.usage.total_tokens"
    KB_REQUEST_MODEL = "kb.request.model"

    # Span attributes
    TRACE_ID = "trace.id"

    # Retriever attributes
    RETRIEVAL_DOCUMENTS = "retrieval.documents"
    RETRIEVAL_DOCUMENT_COUNT = "retrieval.document_count"

    # Langfuse specific attributes
    CUSTOM_TAGS = "langfuse.tags"
    USER_ID = "user.id"
    SESSION_ID = "session.id"
    SPAN_START_TIME = "langfuse.startTime"
    SPAN_END_TIME = "langfuse.endTime"
    SPAN_DURATION = "langfuse.duration_ms"
    SPAN_NAME = "langfuse.span.name"

    # Operation attributes
    OPERATION_NAME = "kb.operation.name"

    # Result attributes
    RESULT_SCORE = "result.{}.score"
    RESULT_SOURCE = "result.{}.source"
    RESULT_CONTENT_LENGTH = "result.{}.content_length"

    # HTTP attributes
    HTTP_STATUS_CODE = "http.status_code"

    # Error attributes
    ERROR_MESSAGE = "error.message"

class SpanKindValues:
    """OpenTelemetry span kind values"""
    CLIENT = "client"

class KBOperationTypes:
    """Knowledge Base operation types"""
    RETRIEVE = "retrieve"
    RETRIEVE_AND_GENERATE = "retrieve_and_generate"

class EventTypes:
    """Trace event types for Amazon Bedrock Knowledge Base"""
    KB_OPERATION = "kbOperationTrace"

    # Subtypes
    KB_INPUT = "kbInvocationInput"
    KB_OUTPUT = "kbInvocationOutput"
