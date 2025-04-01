import copy
import json
import unittest
from unittest import mock
import asyncio
from InlineAgent.agent import ProcessROC
from InlineAgent.agent.confirmation import require_confirmation


def get_current_weather(location: str, state: str, unit: str = "fahrenheit") -> dict:
    """Get the current weather in a given location.

    Args:
        location: The city, e.g., San Francisco
        state: The state eg CA
        unit: The unit to use, e.g., fahrenheit or celsius. Defaults to "fahrenheit"
    """
    # Replace with actual API call or data retrieval
    weather_data = f"Weather in {location}, {state} is 70{unit} and clear skies."
    return weather_data


@require_confirmation
def get_current_weather_confirm(
    location: str, state: str, unit: str = "fahrenheit"
) -> dict:
    """Get the current weather in a given location.

    Args:
        location: The city, e.g., San Francisco
        state: The state eg CA
        unit: The unit to use, e.g., fahrenheit or celsius. Defaults to "fahrenheit"
    """
    # Replace with actual API call or data retrieval
    weather_data = f"Weather in {location}, {state} is 70{unit} and clear skies."
    return weather_data


def get_lat_long(place: str) -> dict:
    """Returns the latitude and longitude for a given place name as a dict object of python.

    Args:
        place: City of the location
    """
    return json.dumps({"lat": 40.7128, "long": 74.0060})


@require_confirmation
def get_lat_long_confirm(place: str) -> dict:
    """Returns the latitude and longitude for a given place name as a dict object of python.

    Args:
        place: City of the location
    """
    return json.dumps({"lat": 40.7128, "long": 74.0060})


def web_search(search_term: str):
    """Search a term in the public Internet. Useful for getting up to date information.

    Args:
        search_term: Term to search in the Internet
    """

    return "Bedrock is the fastes way to build genAi applications"


@require_confirmation
def web_search_confirm(search_term: str):
    """Search a term in the public Internet. Useful for getting up to date information.

    Args:
        search_term: Term to search in the Internet
    """

    return "Bedrock is the fastes way to build genAi applications"


tools_without_confirmation = {
    "get_lat_long": get_lat_long,
    "get_current_weather": get_current_weather,
    "web_search": web_search,
}


event_without_confirmation_one_tool_invoke = dict()

event_without_confirmation_one_tool_invoke["returnControl"] = {
    "invocationInputs": [
        {
            "functionInvocationInput": {
                "actionGroup": "WeatherActionGroup",
                "parameters": [
                    {"name": "place", "type": "string", "value": "New York City"},
                ],
                "function": "get_lat_long",
                "actionInvocationType": "RESULT",
                "agentId": "INLINE_AGENT",
            }
        }
    ],
    "invocationId": "c7d427d4-ee37-4655-ad9c-ef2fb55dd2c7",
}
output_without_confirmation_one_tool_invoke = {
    "returnControlInvocationResults": [
        {
            "functionResult": {
                "actionGroup": "WeatherActionGroup",
                "agentId": "INLINE_AGENT",
                "function": "get_lat_long",
                "responseBody": {"TEXT": {"body": '{"lat": 40.7128, "long": 74.006}'}},
            }
        }
    ],
    "invocationId": "c7d427d4-ee37-4655-ad9c-ef2fb55dd2c7",
}


event_without_confirmation_two_tool_invoke = dict()

event_without_confirmation_two_tool_invoke["returnControl"] = {
    "invocationInputs": [
        {
            "functionInvocationInput": {
                "actionGroup": "WeatherActionGroup",
                "parameters": [
                    {"name": "place", "type": "string", "value": "New York City"}
                ],
                "function": "get_lat_long",
                "actionInvocationType": "RESULT",
                "agentId": "INLINE_AGENT",
            }
        },
        {
            "functionInvocationInput": {
                "actionGroup": "WeatherActionGroup",
                "parameters": [
                    {"name": "location", "type": "string", "value": "New York City"},
                    {"name": "state", "type": "string", "value": "New York"},
                ],
                "function": "get_current_weather",
                "actionInvocationType": "RESULT",
                "agentId": "INLINE_AGENT",
            }
        },
    ],
    "invocationId": "c7d427d4-ee37-4655-ad9c-ef2fb55dd2c7",
}
output_without_confirmation_two_tool_invoke = {
    "returnControlInvocationResults": [
        {
            "functionResult": {
                "actionGroup": "WeatherActionGroup",
                "agentId": "INLINE_AGENT",
                "function": "get_lat_long",
                "responseBody": {"TEXT": {"body": '{"lat": 40.7128, "long": 74.006}'}},
            }
        },
        {
            "functionResult": {
                "actionGroup": "WeatherActionGroup",
                "agentId": "INLINE_AGENT",
                "function": "get_current_weather",
                "responseBody": {
                    "TEXT": {
                        "body": f"Weather in New York City, New York is 70fahrenheit and clear skies."
                    }
                },
            }
        },
    ],
    "invocationId": "c7d427d4-ee37-4655-ad9c-ef2fb55dd2c7",
}


tools_with_confirmation = {
    "get_current_weather": get_current_weather_confirm,
    "get_lat_long": get_lat_long_confirm,
    "web_search": web_search_confirm,
}

event_with_confirmation_one_tool_invoke = dict()

event_with_confirmation_one_tool_invoke["returnControl"] = {
    "invocationInputs": [
        {
            "functionInvocationInput": {
                "actionGroup": "WeatherActionGroup",
                "parameters": [
                    {"name": "location", "type": "string", "value": "New York City"},
                    {"name": "state", "type": "string", "value": "NY"},
                ],
                "function": "get_current_weather",
                "actionInvocationType": "USER_CONFIRMATION_AND_RESULT",
                "agentId": "INLINE_AGENT",
            }
        }
    ],
    "invocationId": "659a026e-c193-4f8d-9dd8-4d6ab0bb585e-uc-result",
}

output_with_confirmation_one_tool_invoke = {
    "returnControlInvocationResults": [
        {
            "functionResult": {
                "actionGroup": "WeatherActionGroup",
                "agentId": "INLINE_AGENT",
                "function": "get_current_weather",
                "responseBody": {
                    "TEXT": {
                        "body": "Weather in New York City, NY is 70fahrenheit and clear skies."
                    }
                },
                "confirmationState": "CONFIRM",
            }
        }
    ],
    "invocationId": "659a026e-c193-4f8d-9dd8-4d6ab0bb585e-uc-result",
}


output_with_confirmation_one_tool_invoke_deny = {
    "returnControlInvocationResults": [
        {
            "functionResult": {
                "actionGroup": "WeatherActionGroup",
                "agentId": "INLINE_AGENT",
                "function": "get_current_weather",
                "responseBody": {
                    "TEXT": {
                        "body": "Access Denied to this function. Do not try again."
                    }
                },
                "confirmationState": "DENY",
            }
        }
    ],
    "invocationId": "659a026e-c193-4f8d-9dd8-4d6ab0bb585e-uc-result",
}

event_only_confirmation_one_tool_invoke = dict()
event_only_confirmation_one_tool_invoke["returnControl"] = {
    "invocationInputs": [
        {
            "functionInvocationInput": {
                "actionGroup": "WeatherActionGroup",
                "parameters": [
                    {"name": "location", "type": "string", "value": "New York City"},
                    {"name": "state", "type": "string", "value": "NY"},
                ],
                "function": "get_current_weather",
                "actionInvocationType": "USER_CONFIRMATION",
                "agentId": "AGENT",
            }
        }
    ],
    "invocationId": "659a026e-c193-4f8d-9dd8-4d6ab0bb585e-uc-result",
}

output_only_confirmation_one_tool_invoke = {
    "returnControlInvocationResults": [
        {
            "functionResult": {
                "actionGroup": "WeatherActionGroup",
                "agentId": "AGENT",
                "function": "get_current_weather",
                "confirmationState": "CONFIRM",
            }
        }
    ],
    "invocationId": "659a026e-c193-4f8d-9dd8-4d6ab0bb585e-uc-result",
}


invoke_roc_function_confirm_functionInvocationInput = {
    "actionGroup": "WeatherActionGroup",
    "parameters": [
        {"name": "place", "type": "string", "value": "New York City"},
        {"name": "state", "type": "string", "value": "New York"},
    ],
    "function": "get_current_weather",
    "actionInvocationType": "USER_CONFIRMATION_AND_RESULT",
    "agentId": "INLINE_AGENT",
}

invoke_roc_function_confirm_parameters = {"location": "New York City", "state": "NY"}

output_invoke_roc_function_confirm = {
    "actionGroup": "WeatherActionGroup",
    "agentId": "INLINE_AGENT",
    "function": "get_current_weather",
    "responseBody": {
        "TEXT": {
            "body": "Weather in New York City, NY is 70fahrenheit and clear skies."
        }
    },
    "confirmationState": "CONFIRM",
}

invoke_roc_function_functionInvocationInput = {
    "actionGroup": "WeatherActionGroup",
    "parameters": [
        {"name": "place", "type": "string", "value": "New York City"},
        {"name": "state", "type": "string", "value": "NY"},
    ],
    "function": "get_current_weather",
    "actionInvocationType": "RESULT",
    "agentId": "INLINE_AGENT",
}

output_invoke_roc_function_without_confirm = {
    "actionGroup": "WeatherActionGroup",
    "agentId": "INLINE_AGENT",
    "function": "get_current_weather",
    "responseBody": {
        "TEXT": {
            "body": "Weather in New York City, NY is 70fahrenheit and clear skies."
        }
    },
}


class TestProcessROC(unittest.IsolatedAsyncioTestCase):
    maxDiff = None

    async def test___init___1(self):
        tools = copy.deepcopy(tools_without_confirmation)
        event = copy.deepcopy(event_without_confirmation_one_tool_invoke)

        inlineSessionState = {"returnControlInvocationResults": []}

        with self.assertRaises(ValueError) as context:
            await ProcessROC.process_roc(
                inlineSessionState=inlineSessionState,
                roc_event=event["returnControl"],
                tool_map=tools,
            )

    async def test___init___2(self):
        tools = copy.deepcopy(tools_without_confirmation)
        event = copy.deepcopy(event_without_confirmation_one_tool_invoke)

        inlineSessionState = {"invocationId": "MOCKID"}
        with self.assertRaises(ValueError) as context:
            await ProcessROC.process_roc(
                inlineSessionState=inlineSessionState,
                roc_event=event["returnControl"],
                tool_map=tools,
            )

    async def test___init___3(self):

        roc_event = dict()
        roc_event["invocationId"] = "MOCKID"
        roc_event["invocationInputs"] = []
        await ProcessROC.process_roc(
            inlineSessionState=dict(),
            roc_event=roc_event,
            tool_map=dict(),
        )

    async def test_without_confirm_1(self):
        tools = copy.deepcopy(tools_without_confirmation)
        event = copy.deepcopy(event_without_confirmation_one_tool_invoke)

        inlineSessionState = dict()

        session_state_output = await ProcessROC.process_roc(
            inlineSessionState=inlineSessionState,
            roc_event=event["returnControl"],
            tool_map=tools,
        )
        self.assertEqual(
            session_state_output, output_without_confirmation_one_tool_invoke
        )
        self.assertEqual(tools, tools_without_confirmation)
        self.assertEqual(inlineSessionState, dict())

    async def test_without_confirm_2(self):
        tools = copy.deepcopy(tools_without_confirmation)
        event = copy.deepcopy(event_without_confirmation_two_tool_invoke)

        inlineSessionState = dict()

        session_state_output = await ProcessROC.process_roc(
            inlineSessionState=inlineSessionState,
            roc_event=event["returnControl"],
            tool_map=tools,
        )
        self.assertEqual(
            session_state_output, output_without_confirmation_two_tool_invoke
        )
        self.assertEqual(tools, tools_without_confirmation)
        self.assertEqual(inlineSessionState, dict())

    async def test_with_confirm_1(self):

        tools = copy.deepcopy(tools_with_confirmation)
        event = copy.deepcopy(event_with_confirmation_one_tool_invoke)

        inlineSessionState = dict()
        with mock.patch("builtins.print") as mock_print:
            with mock.patch("builtins.input", return_value="y") as mock_input:
                session_state_output = await ProcessROC.process_roc(
                    inlineSessionState=inlineSessionState,
                    roc_event=event["returnControl"],
                    tool_map=tools,
                )
                self.assertEqual(
                    session_state_output, output_with_confirmation_one_tool_invoke
                )
                self.assertEqual(tools, tools_with_confirmation)
                self.assertEqual(inlineSessionState, dict())

    async def test_with_confirm_2(self):

        tools = copy.deepcopy(tools_with_confirmation)
        event = copy.deepcopy(event_with_confirmation_one_tool_invoke)

        inlineSessionState = dict()
        with mock.patch("builtins.print") as mock_print:
            with mock.patch("builtins.input", return_value="n") as mock_input:
                session_state_output = await ProcessROC.process_roc(
                    inlineSessionState=inlineSessionState,
                    roc_event=event["returnControl"],
                    tool_map=tools,
                )
                self.assertEqual(
                    session_state_output, output_with_confirmation_one_tool_invoke_deny
                )
                self.assertEqual(tools, tools_with_confirmation)
                self.assertEqual(inlineSessionState, dict())

    async def test_with_confirm_3(self):

        event = copy.deepcopy(event_only_confirmation_one_tool_invoke)

        inlineSessionState = dict()
        with mock.patch("builtins.print") as mock_print:
            with mock.patch("builtins.input", return_value="y") as mock_input:
                session_state_output = await ProcessROC.process_roc(
                    inlineSessionState=inlineSessionState,
                    roc_event=event["returnControl"],
                    tool_map=dict(),
                )
                self.assertEqual(
                    session_state_output, output_only_confirmation_one_tool_invoke
                )
                self.assertEqual(inlineSessionState, dict())

    async def test_invoke_roc_function_1(self):

        functionResult = await ProcessROC.invoke_roc_function(
            functionInvocationInput=invoke_roc_function_confirm_functionInvocationInput,
            tool_to_invoke=tools_with_confirmation["get_current_weather"],
            confirm="CONFIRM",
            parameters=invoke_roc_function_confirm_parameters,
        )

        self.assertEqual(functionResult, output_invoke_roc_function_confirm)

    async def test_invoke_roc_function_2(self):

        functionResult = await ProcessROC.invoke_roc_function(
            functionInvocationInput=invoke_roc_function_functionInvocationInput,
            tool_to_invoke=tools_without_confirmation["get_current_weather"],
            confirm=None,
            parameters=invoke_roc_function_confirm_parameters,
        )
        self.assertEqual(functionResult, output_invoke_roc_function_without_confirm)


if __name__ == "__main__":
    unittest.main()
