class SpanAttributes:

    OPERATION_NAME = "gen_ai.operation.name"
    SYSTEM = "gen_ai.system"
    AGENT_ID = "gen_ai.agent.id"
    AGENT_NAME = "gen_ai.agent.name"

    COMPLETION = "gen_ai.completion.content"
    COMPLETION_ROLE = "gen_ai.completion.role"

    PROMPT = "gen_ai.prompt.content"
    PROMPT_ROLE = "gen_ai.prompt.role"

    REQUEST_MODEL = "gen_ai.request.model"
    RESPONSE_MODEL = "gen_ai.response.model"

    TEMPERATURE = "gen_ai.request.temperature"
    TOP_K = "gen_ai.request.top_k"
    TOP_P = "gen_ai.request.top_p"

    USAGE_PROMPT_TOKENS = "gen_ai.usage.prompt_tokens"
    USAGE_COMPLETION_TOKENS = "gen_ai.usage.completion_tokens"
