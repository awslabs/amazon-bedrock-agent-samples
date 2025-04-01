from datetime import datetime, timezone
import functools
import logging
import os
from opentelemetry import trace as otel_trace
from termcolor import colored
from rich.console import Console
from rich.markdown import Markdown


from opentelemetry.trace import Status, StatusCode, SpanKind
from openinference.semconv.trace import (
    SpanAttributes as OtelSpanAttributes,
    OpenInferenceSpanKindValues,
)

from .utils import add_citation, get_agent_from_caller_chain
from .semantics import SpanAttributes, SpanName
from .process import ProcessL2Trace
from .settings_management import ObservabilityConfig
from .span_manager import SpanManager
from .utils import json_safe


from InlineAgent.constants import TraceColor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

config = ObservabilityConfig()

tracer = otel_trace.get_tracer(config.BEDROCK_AGENT_TRACER_NAME)

guardrail_span: otel_trace.Span = None
output_stream_guardrail_intervene: bool = False
is_guardrail: bool = False


def observe(show_traces: bool = True, save_traces: bool = False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(
            inputText: str,
            sessionId: str,
            **kwargs,
        ):
            global guardrail_span
            global output_stream_guardrail_intervene
            global is_guardrail
            # Extract tracing parameters
            user_id = kwargs.pop("user_id", "anonymous")
            tags = kwargs.pop("tags", [])

            agent_id = kwargs.get("agentId", "")
            agent_alias_id = kwargs.get("agentAliasId", "")
            agent_name = kwargs.pop("agent_name", "")

            if not agent_id or not agent_alias_id:
                # TODO: Warning
                pass

            stream_final_response = kwargs.get(
                "streamingConfigurations", {"streamFinalResponse": False}
            )
            
            stream_final_response= stream_final_response["streamFinalResponse"]
            span_manager = SpanManager()

            time_before_call = datetime.now(timezone.utc)
            time_after_call = None

            if config.PRODUCE_BEDROCK_OTEL_TRACES:
                root_agent_span = span_manager.create_agent_span_return(
                    agent_session_id=sessionId,
                    caller_chain=[
                        {
                            "agentAliasArn": f"arn:aws:bedrock:agent:agent-alias/{agent_id}/{agent_alias_id}"
                        }
                    ],
                    # start_time=int(time_before_call.timestamp() * 1e9),
                    attributes={
                        OtelSpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.AGENT.value,
                        OtelSpanAttributes.INPUT_VALUE: inputText,
                        SpanAttributes.AGENT_ID.value: agent_id,
                        SpanAttributes.AGENT_ALIAS_ID.value: agent_alias_id,
                        OtelSpanAttributes.TAG_TAGS: tags,
                        OtelSpanAttributes.USER_ID: user_id,
                        OtelSpanAttributes.TOOL_PARAMETERS: json_safe(kwargs),
                        OtelSpanAttributes.SESSION_ID: sessionId,
                        "langfuse.tags": tags,
                        OtelSpanAttributes.LLM_SYSTEM: "aws.bedrock",
                    },
                    name=f"Agent {agent_id}:{agent_alias_id}",
                )

            agent_answer = str()
            cite = None
            citations = list()
            total_input_tokens = 0
            total_output_tokens = 0
            total_llm_calls = 0
            try:
                response = func(
                    inputText=inputText,
                    sessionId=sessionId,
                    **kwargs,
                )

                event_stream = response["completion"]

                for event in event_stream:
                    if "files" in event:
                        files_event = event["files"]

                        files_list = files_event["files"]
                        for idx, this_file in enumerate(files_list):
                            file_bytes = this_file["bytes"]

                            # save bytes to file, given the name of file and the bytes

                            directory_path = os.path.join(os.getcwd(), "output")
                            if not os.path.exists(directory_path):
                                try:
                                    os.makedirs(directory_path, exist_ok=True)
                                except OSError as e:
                                    print(f"Error creating directory output: {e}")
                                    raise

                            if not os.path.exists(
                                os.path.join(directory_path, str(sessionId))
                            ):
                                try:
                                    os.makedirs(
                                        os.path.join(directory_path, str(sessionId)),
                                        exist_ok=True,
                                    )
                                except OSError as e:
                                    print(f"Error creating directory output: {e}")
                                    raise

                            file_name = os.path.join(
                                directory_path, str(sessionId), this_file["name"]
                            )
                            with open(file_name, "wb") as f:
                                f.write(file_bytes)

                            if config.PRODUCE_BEDROCK_OTEL_TRACES:
                                with open(file_name, "rb") as f:
                                    root_agent_span.set_attribute(
                                        SpanAttributes.FILES.value + str(idx + 1),
                                        f.read().decode("utf8", errors="ignore"),
                                    )

                        if show_traces:
                            console = Console()
                            print("\n\n")
                            console.print(
                                Markdown("**Files saved in output directory**")
                            )

                    if "returnControl" in event:
                        if config.PRODUCE_BEDROCK_OTEL_TRACES:

                            roc_span = tracer.start_span(
                                name="Return of Control",
                                kind=SpanKind.CLIENT,
                                attributes={
                                    SpanAttributes.RETURN_CONTROL.value: json_safe(
                                        event["returnControl"]
                                    )
                                },
                                context=otel_trace.set_span_in_context(root_agent_span),
                            )
                            roc_span.set_status(Status(StatusCode.OK))
                            roc_span.end()

                    if "trace" in event:

                        trace_data = event["trace"]

                        if "trace" in trace_data:
                            if "guardrailTrace" in trace_data["trace"]:
                                session_id = trace_data["sessionId"]
                                caller_chain = trace_data["callerChain"]
                                guardrail_trace = trace_data["trace"]["guardrailTrace"]
                                sub_agent_id, sub_agent_alias_id = (
                                    get_agent_from_caller_chain(
                                        caller_chain=caller_chain, index=-1
                                    )
                                )

                                if (
                                    sub_agent_id == agent_id
                                    and sub_agent_alias_id == agent_alias_id
                                ):
                                    is_guardrail = True

                                if "inputAssessments" in guardrail_trace:

                                    if config.PRODUCE_BEDROCK_OTEL_TRACES:
                                        agent_span = span_manager.create_agent_span_return(
                                            agent_session_id=session_id,
                                            caller_chain=caller_chain,
                                            # start_time=int(event_time.timestamp() * 1e9),
                                            attributes={
                                                OtelSpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.AGENT.value,
                                                SpanAttributes.AGENT_ID.value: sub_agent_id,
                                                SpanAttributes.AGENT_ALIAS_ID.value: sub_agent_alias_id,
                                                OtelSpanAttributes.LLM_SYSTEM: "aws.bedrock",
                                                OtelSpanAttributes.SESSION_ID: session_id,
                                            },
                                            name=f"Agent {agent_id}:{agent_alias_id}",
                                        )

                                    if guardrail_trace["action"] == "INTERVENED":
                                        agent_answer = str()

                                    if config.PRODUCE_BEDROCK_OTEL_TRACES:
                                        guardrail_span = tracer.start_span(
                                            name=SpanName.GUARDRAIL.value,
                                            kind=SpanKind.CLIENT,
                                            attributes={
                                                OtelSpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.GUARDRAIL.value,
                                                SpanAttributes.GUARDRAIL_ACTION.value: guardrail_trace[
                                                    "action"
                                                ],
                                            },
                                            context=otel_trace.set_span_in_context(
                                                agent_span
                                            ),
                                        )
                                        guardrail_span.set_attributes(
                                            {
                                                OtelSpanAttributes.INPUT_VALUE: json_safe(
                                                    guardrail_trace["inputAssessments"]
                                                ),
                                                OtelSpanAttributes.INPUT_MIME_TYPE: "application/json",
                                            }
                                        )

                                        guardrail_span.set_status(Status(StatusCode.OK))
                                        guardrail_span.end()
                                        guardrail_span = None

                                if "outputAssessments" in guardrail_trace:
                                    if config.PRODUCE_BEDROCK_OTEL_TRACES:
                                        if stream_final_response is False:
                                            if (
                                                guardrail_trace["action"]
                                                == "INTERVENED"
                                            ):
                                                agent_answer = str()

                                            guardrail_span = tracer.start_span(
                                                name=SpanName.GUARDRAIL.value,
                                                kind=SpanKind.CLIENT,
                                                attributes={
                                                    OtelSpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.GUARDRAIL.value,
                                                    SpanAttributes.GUARDRAIL_ACTION.value: guardrail_trace[
                                                        "action"
                                                    ],
                                                },
                                                context=otel_trace.set_span_in_context(
                                                    span_manager.spans[
                                                        session_id
                                                    ].agent_span.span
                                                ),
                                            )
                                            guardrail_span.set_attributes(
                                                {
                                                    OtelSpanAttributes.OUTPUT_VALUE: json_safe(
                                                        guardrail_trace[
                                                            "outputAssessments"
                                                        ]
                                                    ),
                                                    OtelSpanAttributes.OUTPUT_MIME_TYPE: "application/json",
                                                }
                                            )
                                            guardrail_span.set_status(
                                                Status(StatusCode.OK)
                                            )
                                            guardrail_span.end()
                                        else:
                                            if (
                                                not guardrail_span
                                                and guardrail_trace["action"]
                                                == "INTERVENED"
                                            ):

                                                if (
                                                    sub_agent_id == agent_id
                                                    and sub_agent_alias_id
                                                    == agent_alias_id
                                                ):
                                                    output_stream_guardrail_intervene = (
                                                        True
                                                    )

                                                guardrail_span = tracer.start_span(
                                                    name=SpanName.GUARDRAIL.value,
                                                    kind=SpanKind.CLIENT,
                                                    attributes={
                                                        OtelSpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.GUARDRAIL.value,
                                                        SpanAttributes.GUARDRAIL_ACTION.value: guardrail_trace[
                                                            "action"
                                                        ],
                                                    },
                                                    context=otel_trace.set_span_in_context(
                                                        span_manager.spans[
                                                            session_id
                                                        ].agent_span.span
                                                    ),
                                                )
                                                guardrail_span.set_attributes(
                                                    {
                                                        OtelSpanAttributes.OUTPUT_VALUE: json_safe(
                                                            guardrail_trace[
                                                                "outputAssessments"
                                                            ]
                                                        ),
                                                        OtelSpanAttributes.OUTPUT_MIME_TYPE: "application/json",
                                                    }
                                                )
                                                guardrail_span.set_status(
                                                    Status(StatusCode.OK)
                                                )
                                                guardrail_span.end()

                        input_tokens, output_tokens, llm_calls = (
                            ProcessL2Trace.process_trace_event(
                                trace_data=event["trace"],
                                span_manager=span_manager,
                                save_traces=save_traces,
                                session_id=sessionId,
                                show_traces=show_traces,
                            )
                        )
                        total_input_tokens += int(input_tokens)
                        total_output_tokens += int(output_tokens)
                        total_llm_calls += int(llm_calls)

                    # Get Final Answer
                    if "chunk" in event:
                        if "attribution" in event["chunk"]:
                            citations.append(event["chunk"]["attribution"]["citations"])
                            agent_answer, cite = add_citation(
                                citations=event["chunk"]["attribution"]["citations"],
                                cite=1 if not cite else cite,
                            )
                        else:
                            data = event["chunk"]["bytes"]
                            if stream_final_response is True:
                                if output_stream_guardrail_intervene is True:
                                    agent_answer = str()
                                    agent_answer += data.decode("utf8")
                                    print(
                                        colored(
                                            "\n\n\n" + data.decode("utf-8"),
                                            TraceColor.error,
                                        ),
                                        end="",
                                    )
                                else:
                                    agent_answer += data.decode("utf8")
                                    print(
                                        colored(
                                            data.decode("utf-8"),
                                            TraceColor.final_output,
                                        ),
                                        end="",
                                    )
                            else:
                                agent_answer += data.decode("utf8")
                                print(
                                    colored(agent_answer, TraceColor.final_output),
                                    end="",
                                )

                time_after_call = datetime.now(timezone.utc)

                if config.PRODUCE_BEDROCK_OTEL_TRACES:
                    if sessionId not in span_manager.spans:
                        raise RuntimeError("Root Agent span not found")
                    if citations and output_stream_guardrail_intervene is False:
                        root_agent_span.set_attribute(
                            OtelSpanAttributes.RETRIEVAL_DOCUMENTS, json_safe(citations)
                        )

                    if is_guardrail and not guardrail_span:
                        guardrail_span = tracer.start_span(
                            name=SpanName.GUARDRAIL.value,
                            kind=SpanKind.CLIENT,
                            attributes={
                                OtelSpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.GUARDRAIL.value,
                                SpanAttributes.GUARDRAIL_ACTION.value: "NONE",
                            },
                            context=otel_trace.set_span_in_context(root_agent_span),
                        )

                        guardrail_span.set_attributes(
                            {
                                OtelSpanAttributes.OUTPUT_VALUE: json_safe([{}]),
                                OtelSpanAttributes.OUTPUT_MIME_TYPE: "application/json",
                            }
                        )

                        guardrail_span.set_status(Status(StatusCode.OK))
                        guardrail_span.end()
                        guardrail_span = None
                    else:
                        guardrail_span = None

                    root_agent_span.set_attribute(
                        OtelSpanAttributes.OUTPUT_VALUE, agent_answer
                    )
                    root_agent_span.set_attribute(
                        OtelSpanAttributes.OUTPUT_MIME_TYPE, "text/plain"
                    )
                    # End root span

                    if output_stream_guardrail_intervene is True:
                        span_manager.end_all_spans(status_code=StatusCode.OK)
                    else:
                        span_manager.spans[sessionId].agent_span.end_time = int(
                            time_after_call.timestamp() * 1e9
                        )

                    if len(span_manager.spans) > 0:
                        span_manager.end_all_spans(status_code=StatusCode.OK)

            except Exception as e:
                # Handle exceptions

                if config.PRODUCE_BEDROCK_OTEL_TRACES:
                    root_agent_span.record_exception(e)
                    root_agent_span.set_attribute("error.message", str(e))
                    root_agent_span.set_attribute("error.type", e.__class__.__name__)
                    root_agent_span.set_status(Status(StatusCode.ERROR))

                    agent_answer = str()
                    agent_answer = json_safe({"error": str(e), "exception": str(e)})

                    root_agent_span.set_attribute(
                        OtelSpanAttributes.OUTPUT_VALUE, json_safe(agent_answer)
                    )
                    root_agent_span.set_attribute(
                        OtelSpanAttributes.OUTPUT_MIME_TYPE, "application/json"
                    )

                    span_manager.end_all_spans(status_code=StatusCode.ERROR)

                    raise Exception(e)

                else:
                    print(f"An error occurred: {str(e)}")
                    agent_answer = str(e)

                time_after_call = datetime.now(timezone.utc)

            duration = (time_after_call - time_before_call).total_seconds()

            print(
                colored(
                    f"\nAgent made a total of {total_llm_calls} LLM calls, "
                    + f"using {total_input_tokens+total_output_tokens} tokens "
                    + f"(in: {total_input_tokens}, out: {total_output_tokens})"
                    + f", and took {duration} total seconds",
                    TraceColor.stats,
                )
            )

            return agent_answer

        return wrapper

    return decorator
