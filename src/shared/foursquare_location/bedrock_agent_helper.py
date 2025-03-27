import boto3
import json
import asyncio
from typing import Dict, Any, Tuple, Optional, Generator, Union, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from types import TracebackType
from typing_extensions import Self  # For Python < 3.11
from function_calls import parse_function_parameters, invoke_tool

# Define event types
class EventType(Enum):
    CHUNK = "chunk"
    TRACE = "trace"
    FUNCTION_CALL = "function_call"
    FUNCTION_RESULT = "function_result"
    ERROR = "error"
    COMPLETION = "completion"

@dataclass
class AgentEvent:
    type: EventType
    data: Any

class BedrockAgent:
    def __init__(
            self,
            session_id: str,
            model_id: str,
            action_groups: list,
            instructions: str,
            region_name: str = "us-west-2"
    ):
        """Initialize the BedrockAgent with required parameters."""
        self.session_id = session_id
        self.model_id = model_id
        self.action_groups = action_groups
        self.instructions = instructions
        self.invocation_id = None

        # Initialize boto3 client
        session = boto3.Session()
        self.bedrock_rt_client = session.client(
            service_name="bedrock-agent-runtime",
            region_name=region_name
        )

    def _process_response_chunk(self, chunk: Dict) -> AgentEvent:
        """Process a single chunk from the response stream and convert it to an AgentEvent."""
        if 'chunk' in chunk:
            return AgentEvent(
                type=EventType.CHUNK,
                data=chunk['chunk']['bytes'].decode('utf-8')
            )
        elif "trace" in chunk:
            return AgentEvent(
                type=EventType.TRACE,
                data=chunk['trace']['trace']['orchestrationTrace']
            )
        elif 'returnControl' in chunk:
            return AgentEvent(
                type=EventType.FUNCTION_CALL,
                data=chunk['returnControl']
            )
        else:
            return AgentEvent(
                type=EventType.ERROR,
                data=f"Unidentified chunk: {chunk}"
            )

    def _prepare_session_state(self, session_attributes: Dict[str, Any], function_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare the session state dictionary."""
        session_state = {
            'promptSessionAttributes': session_attributes,
        }

        if function_result and self.invocation_id:
            session_state.update({
                'invocationId': self.invocation_id,
                'returnControlInvocationResults': [{
                    'functionResult': function_result
                }]
            })

        return session_state

    @classmethod
    def get_available_models(self):
        return ("us.amazon.nova-pro-v1:0", "us.anthropic.claude-3-5-sonnet-20240620-v1:0")

    def invoke_agent(
            self,
            input_text: str,
            session_attributes: Dict[str, Any],
            function_result: Optional[Dict[str, Any]] = None
    ) -> Generator[AgentEvent, None, None]:
        """Synchronous version of invoke_agent."""
        session_state = self._prepare_session_state(session_attributes, function_result)

        if function_result:
            yield AgentEvent(
                type=EventType.FUNCTION_RESULT,
                data=function_result
            )

        response = self.bedrock_rt_client.invoke_inline_agent(
            instruction=self.instructions,
            foundationModel=self.model_id,
            sessionId=self.session_id,
            endSession=False,
            enableTrace=True,
            inputText=input_text,
            inlineSessionState=session_state,
            actionGroups=self.action_groups
        )

        output = ""
        function_call = None

        for chunk in response['completion']:
            event = self._process_response_chunk(chunk)
            yield event

            if event.type == EventType.CHUNK:
                output += event.data
            elif event.type == EventType.FUNCTION_CALL:
                function_call = event.data

        if function_call:
            function_to_call = parse_function_parameters(function_call)
            self.invocation_id = function_to_call.get('invocationId')

            data, error = invoke_tool(function_to_call)

            if error:
                yield AgentEvent(
                    type=EventType.ERROR,
                    data=error
                )
                return

            function_result = {
                'actionGroup': function_to_call['actionGroup'],
                'function': function_to_call['function'],
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps(data, indent=2)
                    }
                }
            }

            # Recursively call invoke_agent with the function results
            for event in self.invoke_agent(" ", session_attributes, function_result):
                yield event
        else:
            yield AgentEvent(
                type=EventType.COMPLETION,
                data=output
            )
