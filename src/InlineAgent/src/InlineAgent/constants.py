from enum import Enum


USER_INPUT_ACTION_GROUP_NAME = "UserInput"


class Level(Enum):
    CORE = "core"
    ALL = "all"


class TraceColor:
    error = "red"
    final_output = "green"
    cite = "red"
    retrieved_references = "yellow"
    guardrail_trace = "magenta"
    custom_orchestraction_trace = "yellow"
    invocation_input = "magenta"
    invocation_output = "cyan"
    rationale = "blue"
    stats = "red"
    pre_processing = "yellow"
    post_processing = "yellow"
