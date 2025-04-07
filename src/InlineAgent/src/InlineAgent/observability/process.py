import json
import logging
from typing import Any, Dict, Literal

import os
from opentelemetry.trace import StatusCode
from opentelemetry import trace as otel_trace
from openinference.semconv.trace import (
    SpanAttributes as OtelSpanAttributes,
    OpenInferenceSpanKindValues,
)

from InlineAgent.constants import TraceColor

from .utils import (
    get_agent_from_caller_chain,
    get_agent_id_aliasid,
    json_safe,
)
from .semantics import SpanAttributes, SpanName
from .settings_management import ObservabilityConfig
from .span_manager import SpanManager
from .constants import (
    L2Traces,
    L3OrchestrationTraces,
    L3RoutingClassifierTraces,
    L4InvocationInputTraces,
    L4ObservationTraces,
)
from termcolor import colored
from rich.console import Console
from rich.markdown import Markdown

config = ObservabilityConfig()

tracer = otel_trace.get_tracer(config.BEDROCK_AGENT_TRACER_NAME)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class ProcessL2Trace:

    @staticmethod
    def save_trace(trace_data: Dict, session_id: int):
        try:
            directory_path = os.path.join(os.getcwd(), "trace")
            if not os.path.exists(directory_path):
                try:
                    os.makedirs(directory_path, exist_ok=True)
                except OSError as e:
                    print(f"Error creating directory output: {e}")
                    raise

            try:
                with open(
                    os.path.join(directory_path, str(session_id) + ".json"), "r"
                ) as file:
                    data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                # If file doesn't exist or is empty, start with empty list
                data = []

            # Append the new data
            data.append(trace_data)

            # Write back to file with proper formatting
            with open(
                os.path.join(directory_path, str(session_id) + ".json"), "w"
            ) as file:
                json.dump(data, file, indent=2, default=str)

        except Exception as e:
            print(f"An error occurred: {str(e)}")

    @staticmethod
    def process_trace_event(
        trace_data: Dict,
        span_manager: SpanManager,
        save_traces: bool,
        session_id: str,
        show_traces: bool,
    ):
        input_tokens = 0
        output_tokens = 0
        llm_calls = 0

        if save_traces:
            ProcessL2Trace.save_trace(trace_data=trace_data, session_id=session_id)

        if "trace" in trace_data:

            trace = trace_data["trace"]

            # Determine the trace type
            # if L2Traces.guardrailTrace.value in trace:
            #     ProcessL3Trace.process_guardrail_trace(
            #         trace_data=trace_data,
            #         span_manager=span_manager,
            #     )

            if L2Traces.preProcessingTrace.value in trace:
                pre_input_tokens, pre_output_tokens, pre_llm_calls = (
                    ProcessL3Trace.process_pre_processing_trace(
                        trace_data=trace_data,
                        span_manager=span_manager,
                        show_traces=show_traces,
                    )
                )
                input_tokens += pre_input_tokens
                output_tokens += pre_output_tokens
                llm_calls += pre_llm_calls

            if L2Traces.orchestrationTrace.value in trace:
                orch_input_tokens, orch_output_tokens, orch_llm_calls = (
                    ProcessL3Trace.process_orchestration_trace(
                        trace_data=trace_data,
                        span_manager=span_manager,
                        show_traces=show_traces,
                    )
                )
                input_tokens += orch_input_tokens
                output_tokens += orch_output_tokens
                llm_calls += orch_llm_calls

            if L2Traces.postProcessingTrace.value in trace:
                post_input_tokens, post_output_tokens, post_llm_calls = (
                    ProcessL3Trace.process_post_processing_trace(
                        trace_data=trace_data,
                        span_manager=span_manager,
                        show_traces=show_traces,
                    )
                )
                input_tokens += post_input_tokens
                output_tokens += post_output_tokens
                llm_calls += post_llm_calls

            if L2Traces.routingClassifierTrace.value in trace:
                rout_input_tokens, rout_output_tokens, rout_llm_calls = (
                    ProcessL3Trace.process_routing_trace(
                        trace_data=trace_data,
                        span_manager=span_manager,
                        show_traces=show_traces,
                    )
                )
                input_tokens += rout_input_tokens
                output_tokens += rout_output_tokens
                llm_calls += rout_llm_calls

            if "failureTrace" in trace:
                pass

            if "customOrchestrationTrace" in trace:
                pass

        return input_tokens, output_tokens, llm_calls


class ProcessL3Trace:

    @staticmethod
    def process_pre_processing_trace(
        trace_data: Dict, span_manager: SpanManager, show_traces
    ):
        if "trace" in trace_data:

            trace = trace_data["trace"]

            if "preProcessingTrace" in trace:
                pre_processing_trace = trace["preProcessingTrace"]

                if (
                    L3OrchestrationTraces.modelInvocationInput.value
                    in pre_processing_trace
                ):

                    ProcessL4Trace.process_model_invocation_input(
                        trace_data=trace_data,
                        span_manager=span_manager,
                        key="preProcessingTrace",
                        key_name=SpanName.PREPROCESSING.value,
                        show_traces=show_traces,
                    )

                if (
                    L3OrchestrationTraces.modelInvocationOutput.value
                    in pre_processing_trace
                ):
                    input_tokens, output_tokens, llm_calls = (
                        ProcessL4Trace.process_model_invocation_output(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key="preProcessingTrace",
                            show_traces=show_traces,
                        )
                    )
                    return input_tokens, output_tokens, llm_calls
        return 0, 0, 0

    @staticmethod
    def process_post_processing_trace(
        trace_data: Dict, span_manager: SpanManager, show_traces: bool
    ):
        if "trace" in trace_data:

            trace = trace_data["trace"]

            if "postProcessingTrace" in trace:
                post_processing_trace = trace["postProcessingTrace"]

                if (
                    L3OrchestrationTraces.modelInvocationInput.value
                    in post_processing_trace
                ):

                    ProcessL4Trace.process_model_invocation_input(
                        trace_data=trace_data,
                        span_manager=span_manager,
                        key="postProcessingTrace",
                        key_name=SpanName.POSTPROCESSING.value,
                        show_traces=show_traces,
                    )

                if (
                    L3OrchestrationTraces.modelInvocationOutput.value
                    in post_processing_trace
                ):
                    input_tokens, output_tokens, llm_calls = (
                        ProcessL4Trace.process_model_invocation_output(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key="postProcessingTrace",
                            show_traces=show_traces,
                        )
                    )
                    return input_tokens, output_tokens, llm_calls
        return 0, 0, 0

    @staticmethod
    def process_orchestration_trace(
        trace_data: Dict, span_manager: SpanManager, show_traces: bool
    ):
        """Process orchestration trace with proper span hierarchy"""
        if "trace" in trace_data:

            trace = trace_data["trace"]

            if "orchestrationTrace" in trace:
                orchestration_trace = trace["orchestrationTrace"]

                if L3OrchestrationTraces.invocationInput.value in orchestration_trace:
                    ProcessL4Trace.process_invocation_input(
                        trace_data=trace_data,
                        span_manager=span_manager,
                        key="orchestrationTrace",
                        show_traces=show_traces,
                    )

                if (
                    L3OrchestrationTraces.modelInvocationInput.value
                    in orchestration_trace
                ):

                    ProcessL4Trace.process_model_invocation_input(
                        trace_data=trace_data,
                        span_manager=span_manager,
                        key="orchestrationTrace",
                        key_name=SpanName.ORCHESTRACTION.value,
                        show_traces=show_traces,
                    )

                if (
                    L3OrchestrationTraces.modelInvocationOutput.value
                    in orchestration_trace
                ):
                    input_tokens, output_tokens, llm_calls = (
                        ProcessL4Trace.process_model_invocation_output(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key="orchestrationTrace",
                            show_traces=show_traces,
                        )
                    )

                    return input_tokens, output_tokens, llm_calls

                if L3OrchestrationTraces.observation.value in orchestration_trace:
                    ProcessL4Trace.process_observation(
                        trace_data=trace_data,
                        span_manager=span_manager,
                        key="orchestrationTrace",
                        show_traces=show_traces,
                    )

                if L3OrchestrationTraces.rationale.value in orchestration_trace:
                    ProcessL4Trace.process_rationale(
                        trace_data=trace_data,
                        span_manager=span_manager,
                        show_traces=show_traces,
                    )
        return 0, 0, 0

    @staticmethod
    def process_routing_trace(
        trace_data: Dict, span_manager: SpanManager, show_traces: bool
    ):
        if "trace" in trace_data:

            trace = trace_data["trace"]

            if "routingClassifierTrace" in trace:
                routing_classifier_trace = trace["routingClassifierTrace"]

                if (
                    L3RoutingClassifierTraces.invocationInput.value
                    in routing_classifier_trace
                ):
                    ProcessL4Trace.process_invocation_input(
                        trace_data=trace_data,
                        span_manager=span_manager,
                        key="routingClassifierTrace",
                        show_traces=show_traces,
                    )

                if (
                    L3RoutingClassifierTraces.modelInvocationInput.value
                    in routing_classifier_trace
                ):
                    ProcessL4Trace.process_model_invocation_input(
                        trace_data=trace_data,
                        span_manager=span_manager,
                        key="routingClassifierTrace",
                        key_name=SpanName.ROUTING.value,
                        show_traces=show_traces,
                    )

                if (
                    L3RoutingClassifierTraces.modelInvocationOutput.value
                    in routing_classifier_trace
                ):
                    input_tokens, output_tokens, llm_calls = (
                        ProcessL4Trace.process_model_invocation_output(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key="routingClassifierTrace",
                            show_traces=show_traces,
                        )
                    )
                    return input_tokens, output_tokens, llm_calls

                if (
                    L3RoutingClassifierTraces.observation.value
                    in routing_classifier_trace
                ):
                    ProcessL4Trace.process_observation(
                        trace_data=trace_data,
                        span_manager=span_manager,
                        key="routingClassifierTrace",
                        show_traces=show_traces,
                    )
        return 0, 0, 0


class ProcessL4Trace:

    @staticmethod
    def process_model_invocation_input(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal[
            "preProcessingTrace",
            "postProcessingTrace",
            "routingClassifierTrace",
            "orchestrationTrace",
        ],
        key_name: str,
        show_traces: bool,
    ):

        event_time = trace_data["eventTime"]
        caller_chain = trace_data["callerChain"]

        session_id = trace_data["sessionId"]
        agent_version = trace_data["agentVersion"]

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:

                orchestration_trace = trace[key]

                if "modelInvocationInput" in orchestration_trace:
                    model_invocation_input = orchestration_trace["modelInvocationInput"]

                    inference_configuration = model_invocation_input[
                        "inferenceConfiguration"
                    ]

                    model_id = model_invocation_input.get("foundationModel", "")
                    agent_id, agent_alias_id = get_agent_from_caller_chain(
                        caller_chain=caller_chain, index=-1
                    )

                    collaborator_agent_id, collaborator_agent_alias_id = ("", "")

                    if len(caller_chain) > 2:
                        collaborator_agent_id, collaborator_agent_alias_id = (
                            get_agent_from_caller_chain(
                                caller_chain=caller_chain, index=-2
                            )
                        )

                    if config.PRODUCE_BEDROCK_OTEL_TRACES:
                        agent_span = span_manager.create_agent_span_return(
                            agent_session_id=session_id,
                            caller_chain=caller_chain,
                            # start_time=int(event_time.timestamp() * 1e9),
                            attributes={
                                OtelSpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.AGENT.value,
                                OtelSpanAttributes.INPUT_VALUE: json_safe(
                                    model_invocation_input["text"]
                                ),
                                OtelSpanAttributes.INPUT_MIME_TYPE: "application/json",
                                SpanAttributes.AGENT_ID.value: agent_id,
                                SpanAttributes.AGENT_ALIAS_ID.value: agent_alias_id,
                                OtelSpanAttributes.LLM_SYSTEM: "aws.bedrock",
                                OtelSpanAttributes.SESSION_ID: session_id,
                            },
                            name=f"Agent {agent_id}:{agent_alias_id}",
                        )

                        agent_span.set_attribute(
                            SpanAttributes.AGENT_VERSION.value, agent_version
                        )
                        agent_span.set_attribute(
                            SpanAttributes.AGENT_CALLER_CHAIN.value,
                            json_safe(caller_chain),
                        )

                        if model_id:
                            agent_span.set_attribute(
                                OtelSpanAttributes.LLM_MODEL_NAME, model_id
                            )

                        if len(caller_chain) > 1:
                            agent_span.set_attributes(
                                {
                                    OtelSpanAttributes.INPUT_VALUE: json_safe(
                                        model_invocation_input["text"]
                                    ),
                                    OtelSpanAttributes.INPUT_MIME_TYPE: "application/json",
                                }
                            )

                        span_manager.assign_new_l2_return(
                            l2_name=key_name,
                            l3_name=SpanName.LLM.value,
                            agent_session_id=session_id,
                            caller_chain=caller_chain,
                            trace_id=model_invocation_input["traceId"],
                            l2_attributes={
                                OtelSpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                                # OtelSpanAttributes.INPUT_VALUE: json_safe(
                                #     model_invocation_input["text"]
                                # ),
                                # OtelSpanAttributes.INPUT_MIME_TYPE: "application/json",
                            },
                            l3_attributes={
                                OtelSpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.LLM.value,
                                OtelSpanAttributes.INPUT_VALUE: json_safe(
                                    model_invocation_input["text"]
                                ),
                                OtelSpanAttributes.INPUT_MIME_TYPE: "application/json",
                                SpanAttributes.MAX_TOKENS.value: inference_configuration[
                                    "maximumLength"
                                ],
                                SpanAttributes.TEMPERATURE.value: inference_configuration[
                                    "temperature"
                                ],
                                SpanAttributes.TOP_P.value: inference_configuration[
                                    "topP"
                                ],
                                SpanAttributes.TOP_K.value: inference_configuration[
                                    "topK"
                                ],
                                SpanAttributes.STOP_SEQUENCES.value: json_safe(
                                    inference_configuration["stopSequences"]
                                ),
                            },
                            # start_time=int(event_time.timestamp() * 1e9),
                        )

    @staticmethod
    def process_model_invocation_output(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal[
            "preProcessingTrace",
            "postProcessingTrace",
            "routingClassifierTrace",
            "orchestrationTrace",
        ],
        show_traces: bool,
    ):

        event_time = trace_data["eventTime"]
        caller_chain = trace_data["callerChain"]
        session_id = trace_data["sessionId"]
        input_token_count = 0
        output_token_count = 0
        llm_calls = 0

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:

                orchestration_trace = trace[key]

                if "modelInvocationOutput" in orchestration_trace:
                    model_invocation_output = orchestration_trace[
                        "modelInvocationOutput"
                    ]

                    metadata = model_invocation_output["metadata"]

                    if "usage" in metadata:
                        if "inputTokens" in metadata["usage"]:

                            input_token_count = metadata["usage"]["inputTokens"]

                        if "outputTokens" in metadata["usage"]:
                            output_token_count = metadata["usage"]["outputTokens"]

                        llm_calls += 1

                    raw_response = model_invocation_output["rawResponse"]["content"]
                    agent_id, agent_alias_id = get_agent_from_caller_chain(
                        caller_chain=caller_chain, index=-1
                    )

                    try:
                        json_model = json.loads(raw_response)
                        model = (
                            json.loads(raw_response)["model"]
                            if "model" in json.loads(raw_response)
                            else None
                        )
                    except Exception as e:
                        model = None

                    if config.PRODUCE_BEDROCK_OTEL_TRACES:
                        span_manager.spans[session_id].l3_span[
                            f"{agent_id}:{agent_alias_id}"
                        ].span.set_attributes(
                            attributes={
                                OtelSpanAttributes.OUTPUT_VALUE: json_safe(
                                    raw_response
                                ),
                                OtelSpanAttributes.OUTPUT_MIME_TYPE: "application/json",
                                OtelSpanAttributes.LLM_TOKEN_COUNT_PROMPT: input_token_count,
                                OtelSpanAttributes.LLM_TOKEN_COUNT_COMPLETION: output_token_count,
                            }
                        )

                        is_valid_pre = True
                        if "parsedResponse" in model_invocation_output:
                            if "isValid" in model_invocation_output["parsedResponse"]:
                                is_valid_pre = model_invocation_output[
                                    "parsedResponse"
                                ]["isValid"]
                            span_manager.spans[session_id].l3_span[
                                f"{agent_id}:{agent_alias_id}"
                            ].span.set_attributes(
                                attributes={
                                    OtelSpanAttributes.OUTPUT_VALUE: json_safe(
                                        model_invocation_output["parsedResponse"]
                                    ),
                                    OtelSpanAttributes.OUTPUT_MIME_TYPE: "text/plain",
                                    SpanAttributes.RAW_RESPONSE.value: json_safe(
                                        raw_response
                                    ),
                                }
                            )

                        if "reasoningContent" in model_invocation_output:

                            span_manager.spans[session_id].l3_span[
                                f"{agent_id}:{agent_alias_id}"
                            ].span.set_attributes(
                                attributes={
                                    SpanAttributes.RESONING_CONTENT.value: json_safe(
                                        model_invocation_output["reasoningContent"]
                                    )
                                }
                            )

                        if model:
                            span_manager.spans[session_id].l3_span[
                                f"{agent_id}:{agent_alias_id}"
                            ].span.set_attribute(
                                OtelSpanAttributes.LLM_MODEL_NAME,
                                model,
                            )

                        span_manager.delete_l3_span(
                            agent_session_id=session_id,
                            trace_id=model_invocation_output["traceId"],
                            collab_agent_trace_id=f"{agent_id}:{agent_alias_id}",
                            # end_time=int(event_time.timestamp() * 1e9),
                        )

                        if key == "postProcessingTrace" or key == "preProcessingTrace":
                            span_manager.spans[session_id].l2_span.span.set_status(
                                StatusCode(StatusCode.OK)
                            )
                            span_manager.spans[session_id].l2_span.end = True
                            span_manager.spans[session_id].l2_span = None
                            if key == "postProcessingTrace" and len(caller_chain) > 1:
                                span_manager.spans[
                                    session_id
                                ].agent_span.span.set_status(StatusCode(StatusCode.OK))
                                span_manager.spans[session_id].agent_span.end = True
                                del span_manager.spans[session_id]
                            else:
                                if not is_valid_pre:
                                    span_manager.spans[
                                        session_id
                                    ].agent_span.end_time = int(
                                        event_time.timestamp() * 1e9
                                    )

        return input_token_count, output_token_count, llm_calls

    @staticmethod
    def process_invocation_input(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal["routingClassifierTrace", "orchestrationTrace"],
        show_traces: bool,
    ):

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:
                orchestration_trace = trace[key]

                if "invocationInput" in orchestration_trace:
                    invocation_input = orchestration_trace["invocationInput"]

                    if (
                        L4InvocationInputTraces.actionGroupInvocationInput.value
                        in invocation_input
                    ):
                        ProcessL5InvocationInputTrace.process_action_group_invocation_input(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key=key,
                            show_traces=show_traces,
                        )

                    if (
                        L4InvocationInputTraces.agentCollaboratorInvocationInput.value
                        in invocation_input
                    ):
                        ProcessL5InvocationInputTrace.process_agent_collaboration_invocation_input(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key=key,
                            show_traces=show_traces,
                        )

                    if (
                        L4InvocationInputTraces.codeInterpreterInvocationInput.value
                        in invocation_input
                    ):
                        ProcessL5InvocationInputTrace.process_code_interpreter_invocation_input(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key=key,
                            show_traces=show_traces,
                        )

                    if (
                        L4InvocationInputTraces.knowledgeBaseLookupInput.value
                        in invocation_input
                    ):
                        ProcessL5InvocationInputTrace.process_knowledge_base_lookup_input(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key=key,
                            show_traces=show_traces,
                        )

    @staticmethod
    def process_observation(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal["routingClassifierTrace", "orchestrationTrace"],
        show_traces: bool,
    ):
        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:

                orchestration_trace = trace[key]

                if "observation" in orchestration_trace:
                    observation = orchestration_trace["observation"]

                    if (
                        L4ObservationTraces.actionGroupInvocationOutput.value
                        in observation
                    ):
                        ProcessL5Obervation.process_action_group_invocation_output(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key=key,
                            show_traces=show_traces,
                        )

                    if (
                        L4ObservationTraces.agentCollaboratorInvocationOutput.value
                        in observation
                    ):
                        ProcessL5Obervation.process_agent_collaboration_invocation_output(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key=key,
                            show_traces=show_traces,
                        )

                    if (
                        L4ObservationTraces.codeInterpreterInvocationOutput.value
                        in observation
                    ):
                        ProcessL5Obervation.process_code_interpreter_invocation_output(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key=key,
                            show_traces=show_traces,
                        )

                    if (
                        L4ObservationTraces.knowledgeBaseLookupOutput.value
                        in observation
                    ):
                        ProcessL5Obervation.process_knowledge_base_lookup_output(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key=key,
                            show_traces=show_traces,
                        )

                    if L4ObservationTraces.finalResponse.value in observation:
                        ProcessL5Obervation.process_final_response(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key=key,
                            show_traces=show_traces,
                        )

                    if L4ObservationTraces.repromptResponse.value in observation:
                        ProcessL5Obervation.process_reprompt_response(
                            trace_data=trace_data,
                            span_manager=span_manager,
                            key=key,
                            show_traces=show_traces,
                        )

    @staticmethod
    def process_rationale(
        trace_data: Dict, span_manager: SpanManager, show_traces: bool
    ):

        event_time = trace_data["eventTime"]
        caller_chain = trace_data["callerChain"]
        session_id = trace_data["sessionId"]

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if "orchestrationTrace" in trace:

                orchestration_trace = trace["orchestrationTrace"]

                if "rationale" in orchestration_trace:
                    rationale = orchestration_trace["rationale"]

                    text = rationale["text"]
                    agent_id, agent_alias_id = get_agent_from_caller_chain(
                        caller_chain=caller_chain, index=-1
                    )

                    if config.PRODUCE_BEDROCK_OTEL_TRACES:
                        span_manager.spans[session_id].l2_span.span.set_attributes(
                            attributes={SpanName.RATIONALE.value: text}
                        )

                    # span_manager.spans[f"{agent_id}:{agent_alias_id}"].l2_span.end_time=int(event_time.timestamp() * 1e9)


class ProcessL5InvocationInputTrace:

    @staticmethod
    def process_action_group_invocation_input(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal["routingClassifierTrace", "orchestrationTrace"],
        show_traces: bool,
    ):

        event_time = trace_data["eventTime"]
        caller_chain = trace_data["callerChain"]
        session_id = trace_data["sessionId"]

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:

                orchestration_trace = trace[key]

                if "invocationInput" in orchestration_trace:
                    invocation_input = orchestration_trace["invocationInput"]

                    if "actionGroupInvocationInput" in invocation_input:

                        action_group_invocation_input = invocation_input[
                            "actionGroupInvocationInput"
                        ]

                        agent_id, agent_alias_id = get_agent_from_caller_chain(
                            caller_chain=caller_chain, index=-1
                        )

                        name = None
                        parameters = None
                        if "function" in action_group_invocation_input:
                            name = action_group_invocation_input["function"]
                            parameters = action_group_invocation_input["parameters"]
                        elif "apiPath" in action_group_invocation_input:
                            name = action_group_invocation_input["apiPath"]
                            parameters = action_group_invocation_input["requestBody"]

                        if config.PRODUCE_BEDROCK_OTEL_TRACES:
                            span_manager.assign_new_l3_return(
                                agent_session_id=session_id,
                                collab_agent_trace_id=f"{agent_id}:{agent_alias_id}",
                                trace_id=invocation_input["traceId"],
                                # start_time=int(event_time.timestamp() * 1e9),
                                attributes={
                                    OtelSpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.TOOL.value,
                                    OtelSpanAttributes.TOOL_NAME: action_group_invocation_input[
                                        "actionGroupName"
                                    ]
                                    + ":"
                                    + name,
                                    # SpanAttributes.TOOL_ID.value: action_group_invocation_input[
                                    #     "invocationType"
                                    # ],
                                    SpanAttributes.TOOL_TYPE.value: invocation_input[
                                        "invocationType"
                                    ],
                                    OtelSpanAttributes.TOOL_PARAMETERS: json_safe(
                                        parameters
                                    ),
                                    OtelSpanAttributes.INPUT_VALUE: json_safe(
                                        parameters
                                    ),
                                    OtelSpanAttributes.INPUT_MIME_TYPE: "application/json",
                                },
                                name=SpanName.TOOL.value,
                            )

    @staticmethod
    def process_agent_collaboration_invocation_input(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal["routingClassifierTrace", "orchestrationTrace"],
        show_traces: bool,
    ):

        event_time = trace_data["eventTime"]
        caller_chain = trace_data["callerChain"]
        session_id = trace_data["sessionId"]

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:

                orchestration_trace = trace[key]

                if "invocationInput" in orchestration_trace:
                    invocation_input = orchestration_trace["invocationInput"]

                    if "agentCollaboratorInvocationInput" in invocation_input:

                        agent_collaborator_invocation_input = invocation_input[
                            "agentCollaboratorInvocationInput"
                        ]

                        current_agent_id, current_agent_alias_id = (
                            get_agent_from_caller_chain(
                                caller_chain=caller_chain, index=-1
                            )
                        )

                        collab_agent_id, collab_agent_alias_id = get_agent_id_aliasid(
                            agent_collaborator_invocation_input[
                                "agentCollaboratorAliasArn"
                            ]
                        )

                        if config.PRODUCE_BEDROCK_OTEL_TRACES:

                            l3_span = span_manager.assign_new_l3_return(
                                agent_session_id=session_id,
                                collab_agent_trace_id=f"{collab_agent_id}:{collab_agent_alias_id}",
                                trace_id=invocation_input["traceId"],
                                # start_time=int(event_time.timestamp() * 1e9),
                                attributes={
                                    OtelSpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.TOOL.value,
                                    OtelSpanAttributes.TOOL_NAME: agent_collaborator_invocation_input[
                                        "agentCollaboratorName"
                                    ],
                                    SpanAttributes.TOOL_ID.value: agent_collaborator_invocation_input[
                                        "agentCollaboratorAliasArn"
                                    ],
                                    SpanAttributes.TOOL_TYPE.value: "Agent",
                                },
                                name=SpanName.SUB_AGENT.value
                                + f" {collab_agent_id}:{collab_agent_alias_id}",
                            )

                        if "text" in agent_collaborator_invocation_input["input"]:
                            if config.PRODUCE_BEDROCK_OTEL_TRACES:

                                l3_span.set_attribute(
                                    OtelSpanAttributes.INPUT_VALUE,
                                    json_safe(
                                        agent_collaborator_invocation_input["input"][
                                            "text"
                                        ]
                                    ),
                                )

                                l3_span.set_attribute(
                                    OtelSpanAttributes.INPUT_MIME_TYPE,
                                    "application/json",
                                )

                        if (
                            "returnControlResults"
                            in agent_collaborator_invocation_input["input"]
                        ):
                            if config.PRODUCE_BEDROCK_OTEL_TRACES:

                                l3_span.set_attribute(
                                    OtelSpanAttributes.INPUT_VALUE,
                                    json_safe(
                                        agent_collaborator_invocation_input["input"][
                                            "returnControlResults"
                                        ]
                                    ),
                                )

                                l3_span.set_attribute(
                                    OtelSpanAttributes.INPUT_MIME_TYPE,
                                    "application/json",
                                )

    @staticmethod
    def process_code_interpreter_invocation_input(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal["routingClassifierTrace", "orchestrationTrace"],
        show_traces: bool,
    ):

        event_time = trace_data["eventTime"]
        caller_chain = trace_data["callerChain"]
        session_id = trace_data["sessionId"]

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:

                orchestration_trace = trace[key]

                if "invocationInput" in orchestration_trace:
                    invocation_input = orchestration_trace["invocationInput"]

                    if "codeInterpreterInvocationInput" in invocation_input:
                        code_interpreter_invocation_input = invocation_input[
                            "codeInterpreterInvocationInput"
                        ]

                        agent_id, agent_alias_id = get_agent_from_caller_chain(
                            caller_chain=caller_chain, index=-1
                        )

                        if show_traces:
                            print(
                                colored(
                                    f"Code interpreter:", TraceColor.invocation_input
                                )
                            )
                            console = Console()
                            console.print(
                                Markdown(
                                    f"**Generated code**\n```python\n{code_interpreter_invocation_input['code']}\n```"
                                )
                            )

                        if config.PRODUCE_BEDROCK_OTEL_TRACES:
                            span_manager.assign_new_l3_return(
                                agent_session_id=session_id,
                                collab_agent_trace_id=f"{agent_id}:{agent_alias_id}",
                                trace_id=invocation_input["traceId"],
                                # start_time=int(event_time.timestamp() * 1e9),
                                attributes={
                                    OtelSpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.TOOL.value,
                                    OtelSpanAttributes.INPUT_VALUE: code_interpreter_invocation_input[
                                        "code"
                                    ],
                                    OtelSpanAttributes.INPUT_MIME_TYPE: "text/plain",
                                    OtelSpanAttributes.TOOL_PARAMETERS: code_interpreter_invocation_input[
                                        "code"
                                    ],
                                    SpanAttributes.FILES.value: json_safe(
                                        code_interpreter_invocation_input.get(
                                            "files", []
                                        )
                                    ),
                                },
                                name=SpanName.CODE_INTERPRETER.value,
                            )

    @staticmethod
    def process_knowledge_base_lookup_input(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal["routingClassifierTrace", "orchestrationTrace"],
        show_traces: bool,
    ):

        event_time = trace_data["eventTime"]
        caller_chain = trace_data["callerChain"]
        session_id = trace_data["sessionId"]

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:

                orchestration_trace = trace[key]

                if "invocationInput" in orchestration_trace:
                    invocation_input = orchestration_trace["invocationInput"]

                    if "knowledgeBaseLookupInput" in invocation_input:
                        knowledge_base_lookup_input = invocation_input[
                            "knowledgeBaseLookupInput"
                        ]

                        # TODO: UniqueID for tool

                        agent_id, agent_alias_id = get_agent_from_caller_chain(
                            caller_chain=caller_chain, index=-1
                        )

                        if config.PRODUCE_BEDROCK_OTEL_TRACES:

                            span_manager.assign_new_l3_return(
                                agent_session_id=session_id,
                                collab_agent_trace_id=f"{agent_id}:{agent_alias_id}",
                                trace_id=invocation_input["traceId"],
                                # start_time=int(event_time.timestamp() * 1e9),
                                attributes={
                                    OtelSpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.RETRIEVER.value,
                                    OtelSpanAttributes.INPUT_VALUE: knowledge_base_lookup_input[
                                        "text"
                                    ],
                                    OtelSpanAttributes.INPUT_MIME_TYPE: "text/plain",
                                    SpanAttributes.TOOL_ID.value: knowledge_base_lookup_input[
                                        "knowledgeBaseId"
                                    ],
                                    SpanAttributes.FILES.value: knowledge_base_lookup_input[
                                        "text"
                                    ],
                                },
                                name=SpanName.KB.value,
                            )


class ProcessL5Obervation:
    @staticmethod
    def process_action_group_invocation_output(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal["routingClassifierTrace", "orchestrationTrace"],
        show_traces: bool,
    ):

        event_time = trace_data["eventTime"]
        caller_chain = trace_data["callerChain"]
        session_id = trace_data["sessionId"]

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:

                orchestration_trace = trace[key]

                if "observation" in orchestration_trace:
                    observation = orchestration_trace["observation"]

                    if "actionGroupInvocationOutput" in observation:
                        action_group_invocation_output = observation[
                            "actionGroupInvocationOutput"
                        ]

                        agent_id, agent_alias_id = get_agent_from_caller_chain(
                            caller_chain=caller_chain, index=-1
                        )

                        if config.PRODUCE_BEDROCK_OTEL_TRACES:
                            span_manager.spans[session_id].l3_span[
                                f"{agent_id}:{agent_alias_id}"
                            ].span.set_attributes(
                                attributes={
                                    OtelSpanAttributes.OUTPUT_VALUE: action_group_invocation_output[
                                        "text"
                                    ],
                                    OtelSpanAttributes.OUTPUT_MIME_TYPE: "application/json",
                                },
                            )

                            span_manager.delete_l3_span(
                                agent_session_id=session_id,
                                collab_agent_trace_id=f"{agent_id}:{agent_alias_id}",
                                trace_id=observation["traceId"],
                                # end_time=int(event_time.timestamp() * 1e9),
                            )

    @staticmethod
    def process_agent_collaboration_invocation_output(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal["routingClassifierTrace", "orchestrationTrace"],
        show_traces: bool,
    ):

        event_time = trace_data["eventTime"]
        caller_chain = trace_data["callerChain"]
        session_id = trace_data["sessionId"]

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:

                orchestration_trace = trace[key]

                if "observation" in orchestration_trace:
                    observation = orchestration_trace["observation"]

                    if "agentCollaboratorInvocationOutput" in observation:

                        agent_collaborator_invocation_output = observation[
                            "agentCollaboratorInvocationOutput"
                        ]

                        current_agent_id, current_agent_alias_id = (
                            get_agent_from_caller_chain(
                                caller_chain=caller_chain, index=-1
                            )
                        )
                        collab_agent_id, collab_agent_alias_id = get_agent_id_aliasid(
                            agent_collaborator_invocation_output[
                                "agentCollaboratorAliasArn"
                            ]
                        )

                        if "text" in agent_collaborator_invocation_output["output"]:

                            if config.PRODUCE_BEDROCK_OTEL_TRACES:
                                span_manager.spans[session_id].l3_span[
                                    f"{collab_agent_id}:{collab_agent_alias_id}"
                                ].span.set_attributes(
                                    attributes={
                                        OtelSpanAttributes.OUTPUT_VALUE: json_safe(
                                            agent_collaborator_invocation_output[
                                                "output"
                                            ]["text"]
                                        ),
                                        OtelSpanAttributes.OUTPUT_MIME_TYPE: "application/json",
                                    },
                                )

                        if (
                            "returnControlPayload"
                            in agent_collaborator_invocation_output["output"]
                        ):
                            if config.PRODUCE_BEDROCK_OTEL_TRACES:
                                span_manager.spans[session_id].l3_span[
                                    "{collab_agent_id}:{collab_agent_alias_id}"
                                ].span.set_attributes(
                                    attributes={
                                        OtelSpanAttributes.OUTPUT_VALUE: agent_collaborator_invocation_output[
                                            "output"
                                        ][
                                            "returnControlPayload"
                                        ],
                                        OtelSpanAttributes.OUTPUT_MIME_TYPE: "application/json",
                                    },
                                )

                        if config.PRODUCE_BEDROCK_OTEL_TRACES:
                            span_manager.delete_l3_span(
                                agent_session_id=session_id,
                                collab_agent_trace_id=f"{collab_agent_id}:{collab_agent_alias_id}",
                                trace_id=observation["traceId"],
                                # end_time=int(event_time.timestamp() * 1e9),
                            )

    @staticmethod
    def process_code_interpreter_invocation_output(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal["routingClassifierTrace", "orchestrationTrace"],
        show_traces: bool,
    ):

        event_time = trace_data["eventTime"]
        caller_chain = trace_data["callerChain"]
        session_id = trace_data["sessionId"]

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:

                orchestration_trace = trace[key]

                if "observation" in orchestration_trace:
                    observation = orchestration_trace["observation"]

                    if "codeInterpreterInvocationOutput" in observation:
                        code_interpreter_invocation_output = observation[
                            "codeInterpreterInvocationOutput"
                        ]

                        agent_id, agent_alias_id = get_agent_from_caller_chain(
                            caller_chain=caller_chain, index=-1
                        )

                        if (
                            "executionError" in code_interpreter_invocation_output
                            or "executionTimeout" in code_interpreter_invocation_output
                        ):
                            if "executionError" in code_interpreter_invocation_output:
                                if config.PRODUCE_BEDROCK_OTEL_TRACES:
                                    span_manager.spans[session_id].l3_span[
                                        f"{agent_id}:{agent_alias_id}"
                                    ].span.set_attributes(
                                        attributes={
                                            "error.message": code_interpreter_invocation_output[
                                                "executionError"
                                            ],
                                        },
                                    )

                            if "executionTimeout" in code_interpreter_invocation_output:
                                if config.PRODUCE_BEDROCK_OTEL_TRACES:
                                    span_manager.spans[session_id].l3_span[
                                        f"{agent_id}:{agent_alias_id}"
                                    ].span.set_attributes(
                                        attributes={
                                            SpanAttributes.EXECUTION_TIMEOUT.value: code_interpreter_invocation_output[
                                                "executionTimeout"
                                            ],
                                        },
                                    )

                            if config.PRODUCE_BEDROCK_OTEL_TRACES:
                                span_manager.delete_l3_span(
                                    agent_session_id=session_id,
                                    trace_id=observation["traceId"],
                                    # end_time=int(event_time.timestamp() * 1e9),
                                    status=StatusCode.ERROR,
                                    collab_agent_trace_id=f"{agent_id}:{agent_alias_id}",
                                )

                        else:
                            if config.PRODUCE_BEDROCK_OTEL_TRACES:
                                span_manager.spans[session_id].l3_span[
                                    f"{agent_id}:{agent_alias_id}"
                                ].span.set_attributes(
                                    attributes={},
                                )
                                if (
                                    "executionOutput"
                                    in code_interpreter_invocation_output
                                ):
                                    span_manager.spans[session_id].l3_span[
                                        f"{agent_id}:{agent_alias_id}"
                                    ].span.set_attributes(
                                        {
                                            OtelSpanAttributes.OUTPUT_VALUE: json_safe(
                                                code_interpreter_invocation_output[
                                                    "executionOutput"
                                                ]
                                            ),
                                            OtelSpanAttributes.OUTPUT_MIME_TYPE: "application/json",
                                        }
                                    )

                                # if "files" in code_interpreter_invocation_output:
                                #     span_manager.spans[f"{agent_id}:{agent_alias_id}"].l3_span[
                                #     f"{agent_id}:{agent_alias_id}"
                                # ].span.set_attributes({SpanAttributes.FILES.value: json_safe(
                                #             code_interpreter_invocation_output["files"]
                                #         )})

                                span_manager.delete_l3_span(
                                    agent_session_id=session_id,
                                    trace_id=observation["traceId"],
                                    collab_agent_trace_id=f"{agent_id}:{agent_alias_id}",
                                    # end_time=int(event_time.timestamp() * 1e9),
                                )

    @staticmethod
    def process_knowledge_base_lookup_output(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal["routingClassifierTrace", "orchestrationTrace"],
        show_traces: bool,
    ):

        event_time = trace_data["eventTime"]
        caller_chain = trace_data["callerChain"]
        session_id = trace_data["sessionId"]

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:

                orchestration_trace = trace[key]

                if "observation" in orchestration_trace:
                    observation = orchestration_trace["observation"]

                    if "knowledgeBaseLookupOutput" in observation:
                        knowledge_base_lookup_output = observation[
                            "knowledgeBaseLookupOutput"
                        ]

                        agent_id, agent_alias_id = get_agent_from_caller_chain(
                            caller_chain=caller_chain, index=-1
                        )

                        if config.PRODUCE_BEDROCK_OTEL_TRACES:
                            span_manager.spans[session_id].l3_span[
                                f"{agent_id}:{agent_alias_id}"
                            ].span.set_attributes(
                                attributes={
                                    OtelSpanAttributes.RETRIEVAL_DOCUMENTS: json_safe(
                                        knowledge_base_lookup_output[
                                            "retrievedReferences"
                                        ]
                                    ),
                                    OtelSpanAttributes.OUTPUT_VALUE: json_safe(
                                        knowledge_base_lookup_output[
                                            "retrievedReferences"
                                        ]
                                    ),
                                    OtelSpanAttributes.OUTPUT_MIME_TYPE: "application/json",
                                },
                            )

                            span_manager.delete_l3_span(
                                agent_session_id=session_id,
                                trace_id=observation["traceId"],
                                collab_agent_trace_id=f"{agent_id}:{agent_alias_id}",
                                # end_time=int(event_time.timestamp() * 1e9),
                            )

    @staticmethod
    def process_final_response(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal["routingClassifierTrace", "orchestrationTrace"],
        show_traces: bool,
    ):

        event_time = trace_data["eventTime"]
        caller_chain = trace_data["callerChain"]
        session_id = trace_data["sessionId"]

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:

                orchestration_trace = trace[key]

                if "observation" in orchestration_trace:
                    observation = orchestration_trace["observation"]

                    if "finalResponse" in observation:
                        final_response = observation["finalResponse"]

                        agent_id, agent_alias_id = get_agent_from_caller_chain(
                            caller_chain, -1
                        )

                        if config.PRODUCE_BEDROCK_OTEL_TRACES:

                            span_manager.spans[
                                session_id
                            ].agent_span.span.set_attribute(
                                OtelSpanAttributes.OUTPUT_VALUE,
                                json_safe(final_response["text"]),
                            )

                            span_manager.spans[
                                session_id
                            ].agent_span.span.set_attribute(
                                OtelSpanAttributes.OUTPUT_MIME_TYPE, "application/json"
                            )

                            # span_manager.spans[
                            #     f"{agent_id}:{agent_alias_id}"
                            # ].l2_span.span.set_attribute(
                            #     OtelSpanAttributes.OUTPUT_VALUE,
                            #     json_safe(final_response["text"]),
                            # )

                            # span_manager.spans[
                            #     f"{agent_id}:{agent_alias_id}"
                            # ].l2_span.span.set_attribute(
                            #     OtelSpanAttributes.OUTPUT_MIME_TYPE, "application/json"
                            # )

                            # span_manager.spans[f"{agent_id}:{agent_alias_id}"].l2_span.end_time = int(event_time.timestamp() * 1e9)
                            span_manager.spans[session_id].l2_span.end = True
                            span_manager.spans[session_id].l2_span = None

                        if len(caller_chain) != 1:
                            if config.PRODUCE_BEDROCK_OTEL_TRACES:

                                span_manager.spans[session_id].agent_span.end_time = (
                                    int(event_time.timestamp() * 1e9)
                                )
                                # span_manager.delete_agent_span(agent_session_id=session_id)

    @staticmethod
    def process_reprompt_response(
        trace_data: Dict,
        span_manager: SpanManager,
        key: Literal["routingClassifierTrace", "orchestrationTrace"],
        show_traces: bool,
    ):

        event_time = trace_data["eventTime"]
        caller_chain = trace_data["callerChain"]

        if "trace" in trace_data:

            trace = trace_data["trace"]

            if key in trace:

                orchestration_trace = trace[key]

                if "observation" in orchestration_trace:
                    observation = orchestration_trace["observation"]

                    if "repromptResponse" in observation:
                        reprompt_response = observation["repromptResponse"]
                        pass

                        # agent_id, agent_alias_id = get_agent_from_caller_chain(caller_chain, -1)

                        # span_manager.spans[f"{agent_id}:{agent_alias_id}"].l2_span.set_attributes(
                        #     attributes={
                        #         SpanAttributes.OUTPUT.value: json_safe(
                        #             [reprompt_response["text"]]
                        #         ),
                        #         SpanAttributes.TOOL_TYPE.value: reprompt_response[
                        #             "source"
                        #         ],
                        #     },
                        # )
