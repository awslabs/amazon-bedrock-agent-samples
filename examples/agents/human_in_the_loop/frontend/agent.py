import boto3
import time
import pprint
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

agent_id = os.getenv("AGENT_ID")
agent_alias_id = os.getenv("AGENT_ALIAS_ID")
print(f"Agent ID: {agent_id}")
print(f"Agent Alias ID: {agent_alias_id}")

agents_runtime_client = boto3.client("bedrock-agent-runtime")


def InvokeAgent(session_id, prompt):
    """
    Invokes a Bedrock agent with the given parameters.

    Args:
        agent_id (str): The unique identifier of the agent
        agent_alias_id (str): The alias ID of the agent
        session_id (str): Unique session identifier for conversation continuity
        prompt (str): The input text to send to the agent

    Returns:
        str: The agent's response
    """
    try:
        # Create the Bedrock Agent Runtime client
        agents_runtime_client = boto3.client("bedrock-agent-runtime")
        enable_trace: bool = False
        end_session: bool = False

        # "I'd like to book 2 days off with the start date of 2025-01-14"
        print("--------------------------------------------------")
        print(f"Asking agent: {prompt}")
        agentResponse = agents_runtime_client.invoke_agent(
            inputText=prompt,
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            enableTrace=enable_trace,
            endSession=end_session,
        )

        pprint.pprint(agentResponse)
        print("--------------------------------------------------")
        event_stream = agentResponse["completion"]

        completion = ""
        for event in event_stream:
            if "returnControl" in event:
                print("ROC event")
                pprint.pp(event)
                completion = Parse_Roc_Response(event)
            else:
                print("Normal event")
                pprint.pp(event)
                completion = completion + event["chunk"]["bytes"].decode("utf8")
                completion = {"type": "message", "message": completion}

        return completion

    except ClientError as e:
        print(f"Couldn't invoke agent. {e}")
        raise


def CompleteReturnControl(session_id, payload):
    """
    Completes the return control for the given payload.

    Args:
        payload (dict): The payload containing the return control data

    Returns:
        dict: The response from the agent
    """
    try:
        agents_runtime_client = boto3.client("bedrock-agent-runtime")
        enable_trace: bool = False
        print("Completing return control")
        # body = f"User edited their time off request to start on {payload['start_date']} for {payload["number_of_days"]} days. Use this data for a final response."
        body = f"Time off request starting on {payload['start_date']} for {payload["number_of_days"]} days was submitted successfully."

        agentResponse = agents_runtime_client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            enableTrace=enable_trace,
            sessionState={
                "invocationId": payload["invocationId"],
                "returnControlInvocationResults": [
                    {
                        "functionResult": {
                            "actionGroup": payload["actionGroup"],
                            "function": payload["function"],
                            "responseBody": {"TEXT": {"body": body}},
                        }
                    }
                ],
            },
        )
        pprint.pp(agentResponse)

        print("--------------------------------------------------")
        event_stream = agentResponse["completion"]

        completion = ""
        for event in event_stream:
            pprint.pp(event)
            completion = completion + event["chunk"]["bytes"].decode("utf8")

        return body
    except ClientError as e:
        print(f"Couldn't complete return control. {e}")
        raise
    except Exception as e:
        print(f"Couldn't complete return control. {e}")
        raise


def ProvideAgentConfirmation(session_id, payload):
    """
    Provides the agent confirmation for the given payload.

    Args:
        payload (dict): The payload containing the confirmation data

    Returns:
        dict: The response from the agent
    """
    try:
        agents_runtime_client = boto3.client("bedrock-agent-runtime")
        enable_trace: bool = False
        print(f"Providing agent confirmation: {payload['action']}")

        agentResponse = agents_runtime_client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            enableTrace=enable_trace,
            sessionState={
                "invocationId": payload["invocationId"],
                "returnControlInvocationResults": [
                    {
                        "functionResult": {
                            "actionGroup": payload["actionGroup"],
                            "function": payload["function"],
                            "confirmationState": payload["action"],
                            "responseBody": {"TEXT": {"body": ""}},
                        }
                    }
                ],
            },
        )
        pprint.pp(agentResponse)

        print("--------------------------------------------------")
        event_stream = agentResponse["completion"]

        completion = ""
        for event in event_stream:
            pprint.pp(event)
            completion = completion + event["chunk"]["bytes"].decode("utf8")

        return completion
    except ClientError as e:
        print(f"Couldn't provide agent confirmation. {e}")
        return f"Encountered error when processing agent confirmation. session_id: {session_id}"
    except Exception as e:
        print(f"Couldn't provide agent confirmation. {e}")
        raise


def Some_Api_Call(ndays, sdate):
    time.sleep(1)
    print(f"some_api_call: {ndays}, {sdate}")
    print("This could queue up a request that takes a long time and return success")
    return "Time off request was approved"


def Parse_Roc_Response(payload):
    print(f"*****************Parsing ROC****************")
    final_resp = {}
    pprint.pp(payload)
    invocation_inputs = payload["returnControl"]["invocationInputs"]
    invocation_type = invocation_inputs[0]["functionInvocationInput"][
        "actionInvocationType"
    ]
    print(f"type: {invocation_type}, invocationInputs: {invocation_inputs}")
    if invocation_type == "RESULT":
        final_resp["type"] = "returnControl"
    else:
        final_resp["type"] = "confirmation"

    final_resp["invocationId"] = payload["returnControl"]["invocationId"]
    final_resp["actionGroup"] = invocation_inputs[0]["functionInvocationInput"][
        "actionGroup"
    ]
    final_resp["function"] = invocation_inputs[0]["functionInvocationInput"]["function"]
    params = invocation_inputs[0]["functionInvocationInput"]["parameters"]
    for param in params:
        final_resp[param["name"]] = param["value"]
    print(f"*****************Returning****************")
    print(final_resp)
    return final_resp
