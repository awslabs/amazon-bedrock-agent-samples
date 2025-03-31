from dataclasses import dataclass, field
from datetime import datetime, UTC

import json
import uuid
import copy
import os
import boto3
from typing import Callable, Dict, List, Literal, Optional, Tuple, Union
from pydantic import Field
from termcolor import colored
from rich.console import Console
from rich.markdown import Markdown


from InlineAgent.action_group import ActionGroups
from InlineAgent.action_group.action_group import ActionGroup
from InlineAgent.agent.collaborator_agent_instance import CollaboratorAgent
from InlineAgent.constants import (
    USER_INPUT_ACTION_GROUP_NAME,
    TraceColor,
)
from InlineAgent.agent.process_roc import ProcessROC
from InlineAgent.observability import Trace
from InlineAgent.knowledge_base import KnowledgeBasePlugin
from InlineAgent.tools.mcp import MCPServer
from InlineAgent.types import (
    InlineCollaboratorAgentConfig,
    InlineCollaboratorConfigurations,
)


@dataclass
class InlineAgent:
    foundation_model: str
    agent_name: str
    instruction: str
    action_groups: ActionGroups = field(default_factory=list)
    agent_collaboration: Literal["SUPERVISOR", "SUPERVISOR_ROUTER", "DISABLED"] = field(
        default="DISABLED"
    )
    collaborator_configuration: Optional[InlineCollaboratorAgentConfig] = None
    collaborators: Optional[List[Union["InlineAgent", CollaboratorAgent]]] = None
    customer_encryption_key_arn: Optional[str] = None
    guardrail_configuration: Dict = field(default_factory=dict)
    idle_session_ttl_in_seconds: Optional[int] = None
    knowledge_bases: List[KnowledgeBasePlugin] = field(default_factory=list)
    prompt_override_configuration: Dict = field(default_factory=dict)

    profile: str = field(default="default")
    user_input: bool = False
    tool_map: Dict[str, Callable] = None

    @property
    def session(self) -> boto3.Session:
        """Lazy loading of AWS session"""
        return boto3.Session(profile_name=self.profile)

    @property
    def account_id(self) -> str:
        sts_client = self.session.client("sts")
        identity = sts_client.get_caller_identity()
        return identity["Account"]

    @property
    def region(self) -> str:
        return self.session.region_name

    def __post_init__(self):

        if self.knowledge_bases:
            knowledge_bases_list = list()
            for knowledge_base in self.knowledge_bases:
                if not isinstance(knowledge_base, KnowledgeBasePlugin):
                    knowledge_bases_list.append(
                        KnowledgeBasePlugin.model_validate(knowledge_base).to_dict()
                    )
                else:
                    knowledge_bases_list.append(knowledge_base.to_dict())

            self.knowledge_bases = knowledge_bases_list

        if self.action_groups:
            if not isinstance(self.action_groups, ActionGroups):
                for action_group in self.action_groups:
                    ActionGroup.model_validate(action_group)
                self.action_groups = ActionGroups(action_groups=self.action_groups)

            self.tool_map = self.action_groups.tool_map

            self.action_groups = self.action_groups.actionGroups

        if self.user_input:
            if self.action_groups:
                self.action_groups.append(
                    {
                        "actionGroupName": USER_INPUT_ACTION_GROUP_NAME,
                        "parentActionGroupSignature": "AMAZON.UserInput",
                    }
                )
            else:
                self.action_groups = [
                    {
                        "actionGroupName": USER_INPUT_ACTION_GROUP_NAME,
                        "parentActionGroupSignature": "AMAZON.UserInput",
                    }
                ]

        match self.agent_collaboration:
            case "DISABLED" if self.collaborators is not None:
                raise ValueError(
                    "Collaborators should be None if agentCollaboration is DISABLED"
                )
            case "SUPERVISOR" | "SUPERVISOR_ROUTER" if self.collaborators is None:
                raise ValueError(
                    "Collaborators should not be None if agentCollaboration is SUPERVISOR or SUPERVISOR_ROUTER"
                )

        if self.collaborators:
            for collaborator in self.collaborators:
                if not isinstance(collaborator, CollaboratorAgent) and not isinstance(
                    collaborator, InlineAgent
                ):
                    raise ValueError(
                        "collaborators must be either instance of class `InlineAgent` or `CollaboratorAgent`"
                    )
        if self.collaborator_configuration is None:
            self.collaborator_configuration = InlineCollaboratorAgentConfig()
        else:
            if not isinstance(
                self.collaborator_configuration, InlineCollaboratorAgentConfig
            ):
                self.collaborator_configuration = (
                    InlineCollaboratorAgentConfig.model_validate(
                        self.collaborator_configuration
                    )
                )

        if not self.collaborator_configuration.instruction:
            self.collaborator_configuration.instruction = self.instruction

    def get_invoke_params(self) -> Dict:
        invokeParams = dict()
        match self.agent_collaboration:
            case "DISABLED":
                invokeParams = {
                    "actionGroups": self.action_groups,
                    "customerEncryptionKeyArn": self.customer_encryption_key_arn,
                    "foundationModel": self.foundation_model,
                    "guardrailConfiguration": self.guardrail_configuration,
                    "idleSessionTTLInSeconds": self.idle_session_ttl_in_seconds,
                    "instruction": self.instruction,
                    "knowledgeBases": self.knowledge_bases,
                    "promptOverrideConfiguration": self.prompt_override_configuration,
                }
            case "SUPERVISOR" | "SUPERVISOR_ROUTER":

                collaborator_configurations: List[InlineCollaboratorConfigurations] = []
                collaborators_param: List[Dict] = []
                for collaborator in self.collaborators:

                    if isinstance(collaborator, CollaboratorAgent):
                        collaborator_configurations.append(collaborator.to_dict())
                    elif isinstance(collaborator, InlineAgent):
                        collaborator_configurations.append(
                            {
                                "collaboratorInstruction": collaborator.collaborator_configuration.instruction,
                                "collaboratorName": collaborator.agent_name,
                                "relayConversationHistory": collaborator.collaborator_configuration.relayConversationHistory,
                            }
                        )

                        collaborators_param.append(collaborator.get_agent_params())
                invokeParams = {
                    "actionGroups": self.action_groups,
                    "agentCollaboration": self.agent_collaboration,
                    "collaboratorConfigurations": collaborator_configurations,
                    "collaborators": collaborators_param,
                    "customerEncryptionKeyArn": self.customer_encryption_key_arn,
                    "foundationModel": self.foundation_model,
                    "guardrailConfiguration": self.guardrail_configuration,
                    "idleSessionTTLInSeconds": self.idle_session_ttl_in_seconds,
                    "instruction": self.instruction,
                    "knowledgeBases": self.knowledge_bases,
                    "promptOverrideConfiguration": self.prompt_override_configuration,
                }

        return {k: v for k, v in invokeParams.items() if v}

    def get_agent_params(self):
        agentParams = {
            "actionGroups": self.action_groups,
            "agentCollaboration": self.agent_collaboration,
            "agentName": self.agent_name,
            "collaborators": self.collaborators,
            "customerEncryptionKeyArn": self.customer_encryption_key_arn,
            "foundationModel": self.foundation_model,
            "guardrailConfiguration": self.guardrail_configuration,
            "idleSessionTTLInSeconds": self.idle_session_ttl_in_seconds,
            "instruction": self.instruction,
            "knowledgeBases": self.knowledge_bases,
            "promptOverrideConfiguration": self.prompt_override_configuration,
        }
        return {k: v for k, v in agentParams.items() if v}

    async def invoke(
        self,
        input_text: str,
        enable_trace: bool = True,
        session_id: str = str(uuid.uuid4()),
        end_session: bool = False,
        session_state: Dict = None,
        add_citation: bool = False,
        process_response: bool = True,
        truncate_response: int = None,
        streaming_configurations: Dict = {"streamFinalResponse": False},
        bedrock_model_configurations: Dict = {
            "performanceConfig": {"latency": "standard"}
        },
    ):
        if session_state is None:
            session_state = {}

        print(f"SessionId: {session_id}")
        if "returnControlInvocationResults" in session_state:
            raise ValueError(
                "returnControlInvocationResults key is not supported in inlineSessionState"
            )

        if "invocationId" in session_state:
            raise ValueError("invocationId key is not supported in inlineSessionState")

        agent_answer = ""

        bedrock_agent_runtime = boto3.Session(profile_name=self.profile).client(
            "bedrock-agent-runtime"
        )

        inlineSessionState = copy.deepcopy(session_state)

        total_input_tokens = 0
        total_output_tokens = 0
        total_llm_calls = 0

        time_before_call = datetime.now(UTC)
        cite = None
        orch_step = 0
        sub_step = 0

        stream_final_response = streaming_configurations["streamFinalResponse"]
        # print(self.get_invoke_params())
        while not agent_answer:
            if inlineSessionState:
                response = bedrock_agent_runtime.invoke_inline_agent(
                    sessionId=session_id,
                    inputText=input_text,
                    enableTrace=enable_trace,
                    endSession=end_session,
                    inlineSessionState=inlineSessionState,
                    streamingConfigurations=streaming_configurations,
                    bedrockModelConfigurations=bedrock_model_configurations,
                    **self.get_invoke_params(),
                )
            else:
                response = bedrock_agent_runtime.invoke_inline_agent(
                    sessionId=session_id,
                    inputText=input_text,
                    enableTrace=enable_trace,
                    endSession=end_session,
                    streamingConfigurations=streaming_configurations,
                    bedrockModelConfigurations=bedrock_model_configurations,
                    **self.get_invoke_params(),
                )

            if not process_response:
                return response

            inlineSessionState = copy.deepcopy(session_state)

            event_stream = response["completion"]

            try:
                for event in event_stream:
                    # print(json.dumps(event, indent=2, default=str))
                    if "files" in event:
                        files_event = event["files"]

                        console = Console()
                        print("\n\n")
                        console.print(Markdown("**Files saved in output directory**"))

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
                                os.path.join(directory_path, str(session_id))
                            ):
                                try:
                                    os.makedirs(
                                        os.path.join(directory_path, str(session_id)),
                                        exist_ok=True,
                                    )
                                except OSError as e:
                                    print(f"Error creating directory output: {e}")
                                    raise

                            file_name = os.path.join(
                                directory_path, str(session_id), this_file["name"]
                            )
                            with open(file_name, "wb") as f:
                                f.write(file_bytes)

                    if "returnControl" in event:
                        inlineSessionState = await ProcessROC.process_roc(
                            inlineSessionState=inlineSessionState,
                            roc_event=event["returnControl"],
                            tool_map=self.tool_map,
                        )

                    # Process trace
                    if "trace" in event and "trace" in event["trace"] and enable_trace:

                        # print(json.dumps(event["trace"], indent=2))
                        input_tokens, output_tokens, llm_calls = Trace.parse_trace(
                            trace=event["trace"]["trace"],
                            truncateResponse=truncate_response,
                            agentName=self.agent_name,
                        )
                        total_input_tokens += int(input_tokens)
                        total_output_tokens += int(output_tokens)
                        total_llm_calls += int(llm_calls)

                    # Get Final Answer
                    if "chunk" in event:
                        if add_citation:
                            if "attribution" in event["chunk"]:
                                agent_answer, cite = Trace.add_citation(
                                    citations=event["chunk"]["attribution"][
                                        "citations"
                                    ],
                                    cite=1 if not cite else cite,
                                )
                            else:
                                data = event["chunk"]["bytes"]
                                agent_answer += data.decode("utf8")
                                print(
                                    colored(
                                        data.decode("utf8"), TraceColor.final_output
                                    ),
                                    end="",
                                )
                        elif not add_citation:
                            data = event["chunk"]["bytes"]
                            if stream_final_response:
                                agent_answer += data.decode("utf8")
                                print(
                                    colored(
                                        data.decode("utf8"), TraceColor.final_output
                                    ),
                                    end="",
                                )
                            else:
                                agent_answer += data.decode("utf8")
                                print(
                                    colored(agent_answer, TraceColor.final_output),
                                    end="",
                                )

            except Exception as e:
                print(
                    colored("Caught exception while invoking Agent", TraceColor.error)
                )
                print(colored(f"input text: {input_text}", TraceColor.error))
                print(
                    colored(
                        f"request ID: {response['ResponseMetadata']['RequestId']}, retries: {response['ResponseMetadata']['RetryAttempts']}\n",
                        TraceColor.error,
                    )
                )
                print(colored(f"Error: {e}", TraceColor.error))
                raise Exception("Unexpected exception: ", e)

        duration = datetime.now(UTC) - time_before_call

        print(
            colored(
                f"\nAgent made a total of {total_llm_calls} LLM calls, "
                + f"using {total_input_tokens+total_output_tokens} tokens "
                + f"(in: {total_input_tokens}, out: {total_output_tokens})"
                + f", and took {duration.total_seconds():,.1f} total seconds",
                TraceColor.stats,
            )
        )

        return agent_answer
