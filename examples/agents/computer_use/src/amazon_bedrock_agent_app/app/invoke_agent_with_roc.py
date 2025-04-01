from typing import Callable
import boto3

import time
import logging
import json
import aiohttp

import base64


bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name="us-west-2")


ENV_ENDPOINT = "http://environment.computer-use.local:5000/execute"


logging.basicConfig(
    format="[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

from anthropic_local.tools import ToolResult
from anthropic.types import (
    ImageBlockParam,
    MessageParam,
    TextBlockParam,
    ToolUseBlock,
    TextBlock,
    ToolResultBlockParam,
)

versions = ["20250124", "20241022"]


async def invoke_agent_with_roc(
    agent_id: str,
    agent_alias_id: str,
    inputText: str,
    messages: list[MessageParam],
    tool_use_callback: Callable[[ToolUseBlock], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    agent_response_callback: Callable[[TextBlock], None],
    sessionId: str,
    model_id: str,
):
    # sessionId = str(uuid.uuid4())
    agent_answer = str()
    sessionState = {"returnControlInvocationResults": list(), "invocationId": str()}

    # Anthropic defined tools
    # tool_collection = ToolCollection(
    #     ComputerTool(),
    #     BashTool(),
    #     EditTool(),
    # )
    while True:
        # #### Step 1: Invoke Agent ####
        # time.sleep(10)
        tool_result_content: list[ToolResultBlockParam] = []
        if (
            len(sessionState["returnControlInvocationResults"])
            and sessionState["invocationId"]
        ):
            agentResponse = bedrock_agent_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                enableTrace=True,
                sessionId=sessionId,
                sessionState=sessionState,
                inputText="",
            )
            sessionState = {
                "returnControlInvocationResults": list(),
                "invocationId": str(),
            }
        else:
            agentResponse = bedrock_agent_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                enableTrace=True,
                sessionId=sessionId,
                inputText=inputText,
            )

        #### Step 2: Process Stream ####
        event_stream = agentResponse["completion"]
        # logger.info(json.dumps(agentResponse, indent=2, default=str))
        try:
            for event in event_stream:
                if "chunk" in event:
                    data = event["chunk"]["bytes"]
                    # logger.info(f"Final answer ->\n{data.decode('utf8')}")
                    agent_answer = data.decode("utf8")
                    # TODO: Assistant Trace call back: Assistant
                    agent_response_callback(agent_answer)
                    messages.append(
                        {
                            "role": "assistant",
                            "content": agent_answer,
                        }
                    )

                # End event indicates that the request finished successfully
                if "trace" in event:
                    trace = event["trace"]["trace"]
                    # logger.info(json.dumps(event["trace"], indent=2, default=str))
                    if "orchestrationTrace" in trace:
                        orchestrationTrace = trace["orchestrationTrace"]

                        if "invocationInput" in orchestrationTrace:
                            invocationInput = orchestrationTrace["invocationInput"]

                        if "rationale" in orchestrationTrace:
                            agent_response_callback(
                                orchestrationTrace["rationale"]["text"]
                            )
                            messages.append(
                                {
                                    "role": "assistant",
                                    "content": orchestrationTrace["rationale"]["text"],
                                }
                            )

                        # if "modelInvocationInput" in orchestrationTrace:
                        #     modelInvocationInput = orchestrationTrace["modelInvocationInput"]
                        #     if "foundationModel" in modelInvocationInput:
                        #         model_id = modelInvocationInput["foundationModel"]
                        #     print(modelInvocationInput)

                if "returnControl" in event:
                    # logger.info(json.dumps(event["returnControl"], indent=2, default=str))
                    invocationId = event["returnControl"]["invocationId"]
                    if "invocationInputs" in event["returnControl"]:
                        if (len(event["returnControl"]["invocationInputs"])) > 1:
                            agent_response_callback("Calling tools in parallel")
                            messages.append(
                                {
                                    "role": "assistant",
                                    "content": "Calling tools in parallel",
                                }
                            )
                        for invocationInput in event["returnControl"][
                            "invocationInputs"
                        ]:
                            if "functionInvocationInput" in invocationInput:
                                functionInvocationInput = invocationInput[
                                    "functionInvocationInput"
                                ]

                                print(functionInvocationInput)
                                input = dict()

                                for parameter in functionInvocationInput["parameters"]:
                                    if "[" in parameter["value"]:

                                        input[parameter["name"]] = json.loads(
                                            parameter["value"]
                                        )
                                    else:

                                        input[parameter["name"]] = parameter["value"]

                                tool_use_obj = ToolUseBlock(
                                    id=invocationId,
                                    input=input,
                                    name=functionInvocationInput["function"],
                                    type="tool_use",
                                )
                                tool_use_callback(tool_use_obj)
                                messages.append(
                                    {"content": tool_use_obj, "role": "assistant"}
                                )
                                # time.sleep(2)

                                if "claude-3-7-sonnet" in model_id:
                                    version = versions[0]
                                elif "claude-3-5-sonnet" in model_id:
                                    version = versions[1]
                                else:
                                    raise ValueError(f"UnknownModel {model_id}")

                                async with aiohttp.ClientSession() as session:
                                    payload = {
                                        "tool": tool_use_obj.name,
                                        "input": tool_use_obj.input,
                                        "version": version,
                                    }
                                    async with session.post(
                                        ENV_ENDPOINT, json=payload
                                    ) as api_response:
                                        api_result = await api_response.json()
                                        # Convert API response to ToolResult format
                                        logger.info(
                                            json.dumps(
                                                "Received API Result",
                                                indent=2,
                                                default=str,
                                            )
                                        )
                                        logger.info(
                                            json.dumps(
                                                api_result, indent=2, default=str
                                            )
                                        )
                                        result = ToolResult(
                                            output=api_result["result"].get(
                                                "output", ""
                                            ),
                                            error=api_result["result"].get("error", ""),
                                            base64_image=api_result["result"].get(
                                                "base64_image", ""
                                            ),
                                            system=api_result["result"].get(
                                                "system", ""
                                            ),
                                        )

                                tool_result_content.append(
                                    _make_api_tool_result(result, invocationId)
                                )
                                tool_output_callback(result, invocationId)

                                sessionState["invocationId"] = invocationId

                                if result.base64_image:
                                    sessionState[
                                        "returnControlInvocationResults"
                                    ].append(
                                        {
                                            "functionResult": {
                                                "actionGroup": functionInvocationInput[
                                                    "actionGroup"
                                                ],
                                                "responseState": "REPROMPT",
                                                "agentId": functionInvocationInput[
                                                    "agentId"
                                                ],
                                                "function": functionInvocationInput[
                                                    "function"
                                                ],
                                                "responseBody": {
                                                    "IMAGES": {
                                                        "images": [
                                                            {
                                                                "format": "png",
                                                                "source": {
                                                                    "bytes": base64.b64decode(
                                                                        result.base64_image
                                                                    )
                                                                },
                                                            }
                                                        ]
                                                    }
                                                },
                                            }
                                        }
                                    )
                                else:

                                    if result.system or result.output:
                                        text = f"<system>{result.system}</system>\n{result.output}"
                                    else:
                                        text = result.error
                                    sessionState[
                                        "returnControlInvocationResults"
                                    ].append(
                                        {
                                            "functionResult": {
                                                "actionGroup": functionInvocationInput[
                                                    "actionGroup"
                                                ],
                                                "agentId": functionInvocationInput[
                                                    "agentId"
                                                ],
                                                "function": functionInvocationInput[
                                                    "function"
                                                ],
                                                "responseState": "REPROMPT",
                                                "responseBody": {
                                                    "TEXT": {"body": text}
                                                },
                                            }
                                        }
                                    )

                                # break

            if agent_answer and not len(sessionState["returnControlInvocationResults"]):
                return messages
            else:
                messages.append({"content": tool_result_content, "role": "user"})

            # logger.info(json.dumps(messages, indent=2, default=str))

        except Exception as e:
            raise Exception("unexpected event.", e)


def _make_api_tool_result(result: ToolResult, tool_use_id: str) -> ToolResultBlockParam:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content: list[TextBlockParam | ImageBlockParam] | str = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = _maybe_prepend_system_tool_result(result, result.error)
    else:
        if result.output:
            tool_result_content.append(
                {
                    "type": "text",
                    "text": _maybe_prepend_system_tool_result(result, result.output),
                }
            )
        if result.base64_image:
            tool_result_content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result.base64_image,
                    },
                }
            )
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }


def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str):
    if result.system:
        result_text = f"<system>{result.system}</system>\n{result_text}"
    return result_text
