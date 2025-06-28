"""
Core module for Amazon Bedrock Knowledge Bases OpenTelemetry integration.
"""

from .knowledgebase import instrument_kb_operation
from .tracing import flush_telemetry