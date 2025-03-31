from enum import Enum


class SpanAttributes(Enum):
    AGENT_ID = "gen_ai.agent.id"
    AGENT_ALIAS_ID = "bedrock.agent.alias_id"
    SUPERVISOR_NAME = "bedrock.agent.supervisor.name"
    AGENT_VERSION = "bedrock.agent.version"
    AGENT_CALLER_CHAIN = "bedrock.agent.caller_chain"

    MAX_TOKENS = "gen_ai.request.max_tokens"
    TEMPERATURE = "gen_ai.request.temperature"
    TOP_P = "gen_ai.request.top_p"
    TOP_K = "gen_ai.request.top_k"
    STOP_SEQUENCES = "gen_ai.request.stop_sequences"

    TOOL_TYPE = "gen_ai.tool.type"
    TOOL_ID = "gen_ai.tool.call.id"  # invocationId

    FILES = "bedrock.agent.files"

    EXECUTION_TIMEOUT = "bedrock.agent.execution_timeout"

    GUARDRAIL_ACTION = "bedrock.guardrail.action"
    RETURN_CONTROL = "bedrock.agent.return_control"

    RAW_RESPONSE = "bedrock.agent.raw_response"
    RESONING_CONTENT = "bedrock.agent.resoning_content"


class SpanName(Enum):
    ORCHESTRACTION = "Orchestration"
    ROUTING = "RoutingClassifier"
    PREPROCESSING = "PreProcessing"
    POSTPROCESSING = "PostProcessing"
    GUARDRAIL = "Guardrail"
    RATIONALE = "Rationale"
    CODE_INTERPRETER = "Code Interpreter"
    KB = "Knowledge Base"
    LLM = "LLM"
    SUB_AGENT = "Sub Agent"
    TOOL = "Tool"
