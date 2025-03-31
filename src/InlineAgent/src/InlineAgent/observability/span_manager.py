# Class to manage spans

from typing import Dict, Any, Literal, Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind, Span

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationInfo,
    field_validator,
    validate_call,
)

from .utils import get_agent_from_caller_chain


from pydantic import BaseModel
from typing import Dict, Any

tracer = trace.get_tracer("bedrock-agent-tracing")


class SpanModel(BaseModel):
    span: Span
    end_time: int = 0
    end: Optional[bool] = None

    class Config:
        arbitrary_types_allowed = True
        extra = "forbid"
        validate_assignment = True

    @field_validator("end", mode="after")
    @classmethod
    def validate_end(cls, value: bool, info: ValidationInfo):
        # Check if we're trying to set a non-zero end_time
        if value is True:

            SpanModel.process_end(
                span=info.data["span"], end_time=info.data["end_time"]
            )
        return value

    @staticmethod
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def process_end(span: Span, end_time: int):
        if span.is_recording():
            if end_time:
                span.end(end_time=end_time)
            else:
                span.end()


class SpanFamily(BaseModel):
    family: str
    counter: str
    agent_span: SpanModel
    l2_span: Optional[SpanModel] = (
        None  # If counter changes end l2 span, if family changes end l2 span
    )
    l3_span: Dict[str, SpanModel] = {}

    class Config:
        arbitrary_types_allowed = True  # Needed for the Span object
        extra = "forbid"  # Prevents additional fields


class SpanManager(BaseModel):

    spans: Optional[Dict[str, SpanFamily]] = {}
    agent_session_id_dict: Optional[Dict[str, str]] = {}

    class Config:
        arbitrary_types_allowed = True
        extra = "forbid"
        validate_assignment = True

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def create_agent_span_return(
        self,
        agent_session_id: str,
        caller_chain: list,
        # start_time: int,
        attributes: Dict[str, Any],
        name: str,
    ) -> Span:
        # new agent
        parent_span = None

        if agent_session_id in self.spans:
            return self.spans[agent_session_id].agent_span.span

        agent_id, agent_alias_id = get_agent_from_caller_chain(
            caller_chain=caller_chain, index=-1
        )
        collaborator_session_id = str()

        if len(caller_chain) > 1:
            collaborator_agent_id, collaborator_agent_alias_id = (
                get_agent_from_caller_chain(caller_chain=caller_chain, index=-2)
            )
            collaborator_session_id = self.agent_session_id_dict[
                f"{collaborator_agent_id}:{collaborator_agent_alias_id}"
            ]

        if collaborator_session_id in self.spans:
            # print(self.spans)

            if (
                len(self.spans[collaborator_session_id].l3_span)
                and f"{agent_id}:{agent_alias_id}"
                in self.spans[collaborator_session_id].l3_span
                and self.spans[collaborator_session_id]
                .l3_span[f"{agent_id}:{agent_alias_id}"]
                .span
            ):
                parent_span = (
                    self.spans[collaborator_session_id]
                    .l3_span[f"{agent_id}:{agent_alias_id}"]
                    .span
                )
            else:
                raise RuntimeError("L3 span not found while creating sub agent span.")
        else:
            if len(caller_chain) > 1:
                raise RuntimeError(
                    "Collaborator span not found while creating agent span."
                )

        span = tracer.start_span(
            name=name,
            kind=SpanKind.CLIENT,
            attributes=attributes or {},
            context=trace.set_span_in_context(parent_span),
            # start_time=start_time,
        )

        span_family = SpanFamily(
            family="",
            counter="",
            agent_span=SpanModel(span=span),
        )

        self.spans[agent_session_id] = span_family
        self.agent_session_id_dict[f"{agent_id}:{agent_alias_id}"] = agent_session_id

        return span

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def delete_agent_span(
        self,
        agent_session_id: str,
    ) -> Span:
        # new agent
        if agent_session_id not in self.spans:
            raise RuntimeError("Agent span not found while deleting agent span.")

        if self.spans[agent_session_id].l2_span:
            raise RuntimeError("Close l2 span first before clossing agent span")

        if agent_session_id in self.spans[agent_session_id].l3_span:
            raise RuntimeError("Close l3 span first before clossing agent span")

        self.spans[agent_session_id].agent_span.span.set_status(Status(StatusCode.OK))
        # self.spans[agent_session_id].agent_span.end_time = end_time
        self.spans[agent_session_id].agent_span.end = True

        del self.spans[agent_session_id]

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def assign_new_l2_return(
        self,
        agent_session_id: str,
        caller_chain: list,
        trace_id: str,
        l2_attributes: Dict[str, Any],
        l3_attributes: Dict[str, Any],
        l2_name: str,
        l3_name: str,
    ) -> Span:

        agent_id, agent_alias_id = get_agent_from_caller_chain(
            caller_chain=caller_chain, index=-1
        )
        l2_span = None
        if agent_session_id not in self.spans:
            raise RuntimeError("Agent span not found")

        family = trace_id[:36]
        counter = trace_id[37:]

        if self.spans[agent_session_id].family and self.spans[agent_session_id].counter:
            if family != self.spans[agent_session_id].family:
                raise RuntimeError("New Agent span should be assigned first")
            else:
                if counter == self.spans[agent_session_id].counter:
                    return self.spans[agent_session_id].l2_span.span
                else:
                    if (
                        len(self.spans[agent_session_id].l3_span)
                        and self.spans[agent_session_id]
                        .l3_span[f"{agent_id}:{agent_alias_id}"]
                        .span
                    ):

                        self.spans[agent_session_id].l3_span[
                            f"{agent_id}:{agent_alias_id}"
                        ].span.end = True
                        del self.spans[agent_session_id].l3_span[
                            f"{agent_id}:{agent_alias_id}"
                        ]

                    if (
                        self.spans[agent_session_id].l2_span
                        and self.spans[agent_session_id].l2_span.span
                    ):
                        self.spans[agent_session_id].l2_span.end = True
                        self.spans[agent_session_id].l2_span = None

        # Save new l2 span
        l2_span = tracer.start_span(
            name=l2_name,
            kind=SpanKind.CLIENT,
            attributes=l2_attributes or {},
            context=trace.set_span_in_context(
                self.spans[agent_session_id].agent_span.span
            ),
        )

        l3_span = tracer.start_span(
            name=l3_name,
            kind=SpanKind.CLIENT,
            attributes=l3_attributes or {},
            context=trace.set_span_in_context(l2_span),
        )

        self.spans[agent_session_id].l2_span = SpanModel(span=l2_span)

        self.spans[agent_session_id].l3_span.update(
            {f"{agent_id}:{agent_alias_id}": SpanModel(span=l3_span)}
        )

        self.spans[agent_session_id].family = family
        self.spans[agent_session_id].counter = counter

        return l2_span

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def assign_new_l3_return(
        self,
        agent_session_id: str,
        collab_agent_trace_id: str,
        trace_id: str,
        attributes: Dict[str, Any],
        name: str,
    ) -> Span:
        l3_span = None

        if agent_session_id not in self.spans:
            raise RuntimeError("Agent span not found")

        family = trace_id[:36]
        counter = trace_id[37:]

        if family != self.spans[agent_session_id].family:
            raise RuntimeError("New Agent span should be assigned first")

        if counter != self.spans[agent_session_id].counter:
            raise RuntimeError("Assign a new L2 span")

        if not self.spans[agent_session_id].l2_span:
            raise RuntimeError("L2 span does not exists")

        if collab_agent_trace_id in self.spans[agent_session_id].l3_span:
            raise RuntimeError("L3 span already exists")

        # Assign New
        l3_span = tracer.start_span(
            name=name,
            kind=SpanKind.CLIENT,
            attributes=attributes or {},
            context=trace.set_span_in_context(
                self.spans[agent_session_id].l2_span.span
            ),
        )

        self.spans[agent_session_id].l3_span.update(
            {collab_agent_trace_id: SpanModel(span=l3_span)}
        )

        self.agent_session_id_dict[collab_agent_trace_id] = agent_session_id

        return l3_span

    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def delete_l3_span(
        self,
        agent_session_id: str,
        collab_agent_trace_id: str,
        trace_id: str,
        status=StatusCode.OK,
    ) -> Span:
        if agent_session_id not in self.spans:
            raise RuntimeError("Agent span not found")

        family = trace_id[:36]
        counter = trace_id[37:]

        if family != self.spans[agent_session_id].family:
            raise RuntimeError("New Agent span should be assigned first")

        if counter != self.spans[agent_session_id].counter:
            raise RuntimeError("Assign a new L2 span")

        if not self.spans[agent_session_id].l2_span:
            raise RuntimeError("L2 span not found")

        if collab_agent_trace_id not in self.spans[agent_session_id].l3_span:
            raise RuntimeError("L3 span not found")

        self.spans[agent_session_id].l3_span[collab_agent_trace_id].span.set_status(
            Status(status)
        )
        # self.spans[agent_session_id].l3_span.end_time = end_time
        self.spans[agent_session_id].l3_span[collab_agent_trace_id].end = True
        del self.spans[agent_session_id].l3_span[collab_agent_trace_id]

        # self.spans[agent_session_id].l2_span.end_time = end_time

    def end_all_spans(self, status_code: Literal[StatusCode.OK, StatusCode.ERROR]):

        for _, current_span in self.spans.items():

            if current_span.l3_span:
                for _, current_l3_span in current_span.l3_span.items():
                    current_l3_span.span.set_status(StatusCode(StatusCode.OK))
                    current_l3_span.end = True

            current_span.l3_span = None
            if current_span.l2_span:
                current_span.l2_span.span.set_status(StatusCode(status_code))
                current_span.l2_span.end = True
                current_span.l2_span = None

            if current_span.agent_span:
                current_span.agent_span.span.set_status(StatusCode(status_code))
                current_span.agent_span.end = True
                current_span.agent_span = None
            current_span.family = ""
            current_span.counter = ""

        self.spans = {}
