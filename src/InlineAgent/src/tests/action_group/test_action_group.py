import json
import unittest
from unittest.mock import Mock

from InlineAgent.action_group import ActionGroups, ActionGroup
from InlineAgent.constants import USER_INPUT_ACTION_GROUP_NAME
from InlineAgent.tools.mcp import MCPStdio
from InlineAgent.types.action_group import Executor


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


action_group_1_one_tool = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location.",
        "parameters": {
            "location": {
                "type": "string",
                "description": "The city, e.g., San Francisco",
                "required": True,
            },
            "state": {
                "type": "string",
                "description": "The state eg CA",
                "required": True,
            },
            "unit": {
                "type": "string",
                "description": 'The unit to use, e.g., fahrenheit or celsius. Defaults to "fahrenheit"',
                "required": False,
            },
        },
        "requireConfirmation": "DISABLED",
    }
]


class TestActionGroup(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_tool = Mock()
        self.mock_mcp_clients = Mock(spec=MCPStdio)

    def test_executor(self):

        action_group = ActionGroup(
            name=USER_INPUT_ACTION_GROUP_NAME,
            builtin_tools={"parentActionGroupSignature": "AMAZON.UserInput"},
            test=True,
        )

        self.assertEqual(action_group.executor.value, Executor.INBUILT_TOOL.value)

        action_group = ActionGroup(
            name="Weather Action Group", tools=[get_current_weather], test=True
        )
        self.assertEqual(action_group.executor.value, Executor.RETURN_CONTROL.value)

        action_group = ActionGroup(
            name="Weather Action Group",
            lambda_name="Weather",
            function_schema=action_group_1_one_tool,
            test=True,
        )
        self.assertEqual(action_group.executor.value, Executor.LAMBDA.value)

        action_group = ActionGroup(
            name="Weather Action Group",
            api_schema={
                "payload": "openApi.json",
            },
            lambda_name="Weather",
            test=True,
        )
        self.assertEqual(action_group.executor.value, Executor.LAMBDA.value)

        action_group = ActionGroup(
            name="Weather Action Group", mcp_clients=[self.mock_mcp_clients], test=True
        )
        self.assertEqual(action_group.executor.value, Executor.RETURN_CONTROL.value)

    def test_invalid_builtin_tools(self):

        ActionGroup(
            name="Computer use",
            builtin_tools={
                "parentActionGroupSignature": "ANTHROPIC.Computer",
                "parentActionGroupSignatureParams": {
                    "type": "computer_20250124",
                    "display_height_px": "768",
                    "display_width_px": "1024",
                    "display_number": "1",
                },
            },
            test=True,
        )

        with self.assertRaises(ValueError):
            ActionGroup(
                name=USER_INPUT_ACTION_GROUP_NAME,
                builtin_tools={"parentActionGropSignature": "AMAZON.UserInput"},
                executor=Executor.RETURN_CONTROL,
                test=True,
            )
        with self.assertRaises(ValueError):

            ActionGroup(
                name=USER_INPUT_ACTION_GROUP_NAME,
                builtin_tools={
                    "parentActionGroupSignature": "ANTHROPIC.Computer",
                    "parentActionGroupSignatureParams": {
                        "type": "computer_20250124",
                        "display_height_px": "768",
                        "display_width_px": "1024",
                        "display_number": "1",
                    },
                    "mock": "mock",
                },
                test=True,
            )
        with self.assertRaises(ValueError):

            ActionGroup(
                name="Computer use",
                builtin_tools={
                    "parentActionGroupSignature": "ANTHROPIC.Computer",
                    "parentActionGroupSignatureParams": {
                        "type": "computer_20250124",
                        "display_height_px": "768",
                        "display_width_px": "1024",
                        "display_number": "1",
                    },
                },
                tools=[get_current_weather],
                test=True,
            )
        with self.assertRaises(ValueError):

            ActionGroup(
                name="Computer use",
                builtin_tools={
                    "parentActionGroupSignature": "ANTHROPIC.Computer",
                    "parentActionGroupSignatureParams": {
                        "type": "computer_20250124",
                        "display_height_px": "768",
                        "display_width_px": "1024",
                        "display_number": "1",
                    },
                },
                lambda_name="Weather",
                function_schema=action_group_1_one_tool,
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Computer use",
                builtin_tools={
                    "parentActionGroupSignature": "ANTHROPIC.Computer",
                    "parentActionGroupSignatureParams": {
                        "type": "computer_20250124",
                        "display_height_px": "768",
                        "display_width_px": "1024",
                        "display_number": "1",
                    },
                },
                lambda_name="Weather",
                api_schema={
                    "payload": "openApi.json",
                },
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Computer use",
                builtin_tools={
                    "parentActionGroupSignature": "ANTHROPIC.Computer",
                    "parentActionGroupSignatureParams": {
                        "type": "computer_20250124",
                        "display_height_px": "768",
                        "display_width_px": "1024",
                        "display_number": "1",
                    },
                },
                mcp_clients=[self.mock_mcp_clients],
                test=True,
            )

    def test_invalid_mcp_clients(self):
        ActionGroup(
            name="Weather Action Group", mcp_clients=[self.mock_mcp_clients], test=True
        )

        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                mcp_clients=[self.mock_mcp_clients],
                builtin_tools={
                    "parentActionGroupSignature": "ANTHROPIC.Computer",
                    "parentActionGroupSignatureParams": {
                        "type": "computer_20250124",
                        "display_height_px": "768",
                        "display_width_px": "1024",
                        "display_number": "1",
                    },
                },
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                mcp_clients=[self.mock_mcp_clients],
                lambda_name="Weather",
                api_schema={
                    "payload": "openApi.json",
                },
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                mcp_clients=[self.mock_mcp_clients],
                lambda_name="Weather",
                function_schema=action_group_1_one_tool,
                test=True,
            )
        with self.assertRaises(ValueError):

            ActionGroup(
                name="Weather Action Group",
                mcp_clients=[self.mock_mcp_clients],
                tools=[get_current_weather],
                test=True,
            )

    def test_invalid_tools(self):
        ActionGroup(name="Weather Action Group", tools=[get_current_weather])

        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                tools=[get_current_weather],
                builtin_tools={
                    "parentActionGroupSignature": "ANTHROPIC.Computer",
                    "parentActionGroupSignatureParams": {
                        "type": "computer_20250124",
                        "display_height_px": "768",
                        "display_width_px": "1024",
                        "display_number": "1",
                    },
                },
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                tools=[get_current_weather],
                lambda_name="Weather",
                api_schema={
                    "payload": "openApi.json",
                },
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                tools=[get_current_weather],
                lambda_name="Weather",
                function_schema=action_group_1_one_tool,
                test=True,
            )
        with self.assertRaises(ValueError):

            ActionGroup(
                name="Weather Action Group",
                tools=[get_current_weather],
                mcp_clients=[self.mock_mcp_clients],
                test=True,
            )

    def test_invalid_lambda_name(self):
        ActionGroup(
            name="Weather Action Group",
            lambda_name="Weather",
            function_schema=action_group_1_one_tool,
            test=True,
        )

        ActionGroup(
            name="Weather Action Group",
            lambda_name="Weather",
            api_schema={
                "payload": "openApi.json",
            },
            test=True,
        )

        ActionGroup(
            name="Weather Action Group",
            lambda_name="Weather",
            api_schema={
                "s3": {
                    "s3BucketName": "XXXXXXXXXX",
                    "s3ObjectKey": "XXXXXXXXXX",
                },
            },
            test=True,
        )

        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                lambda_name="Weather",
                function_schema=action_group_1_one_tool,
                builtin_tools={
                    "parentActionGroupSignature": "ANTHROPIC.Computer",
                    "parentActionGroupSignatureParams": {
                        "type": "computer_20250124",
                        "display_height_px": "768",
                        "display_width_px": "1024",
                        "display_number": "1",
                    },
                },
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                lambda_name="Weather",
                function_schema=action_group_1_one_tool,
                tools=[get_current_weather],
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                lambda_name="Weather",
                function_schema=action_group_1_one_tool,
                mcp_clients=[self.mock_mcp_clients],
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                lambda_name="Weather",
                api_schema={
                    "payload": "openApi.json",
                },
                builtin_tools={
                    "parentActionGroupSignature": "ANTHROPIC.Computer",
                    "parentActionGroupSignatureParams": {
                        "type": "computer_20250124",
                        "display_height_px": "768",
                        "display_width_px": "1024",
                        "display_number": "1",
                    },
                },
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                lambda_name="Weather",
                api_schema={
                    "payload": "openApi.json",
                },
                tools=[get_current_weather],
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                lambda_name="Weather",
                api_schema={
                    "payload": "openApi.json",
                },
                mcp_clients=[self.mock_mcp_clients],
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                lambda_name="Weather",
                api_schema={
                    "s3": {
                        "s3BucketName": "XXXXXXXXXX",
                        "s3ObjectKey": "XXXXXXXXXX",
                    },
                },
                builtin_tools={
                    "parentActionGroupSignature": "ANTHROPIC.Computer",
                    "parentActionGroupSignatureParams": {
                        "type": "computer_20250124",
                        "display_height_px": "768",
                        "display_width_px": "1024",
                        "display_number": "1",
                    },
                },
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                lambda_name="Weather",
                api_schema={
                    "s3": {
                        "s3BucketName": "XXXXXXXXXX",
                        "s3ObjectKey": "XXXXXXXXXX",
                    },
                },
                tools=[get_current_weather],
                test=True,
            )
        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                lambda_name="Weather",
                api_schema={
                    "s3": {
                        "s3BucketName": "XXXXXXXXXX",
                        "s3ObjectKey": "XXXXXXXXXX",
                    },
                },
                mcp_clients=[self.mock_mcp_clients],
                test=True,
            )

        with self.assertRaises(ValueError):
            ActionGroup(
                name="Weather Action Group",
                lambda_name="Weather",
                api_schema={
                    "payload": "openApi.json",
                    "s3": {
                        "s3BucketName": "XXXXXXXXXX",
                        "s3ObjectKey": "XXXXXXXXXX",
                    },
                },
                test=True,
            )

    def test_executor_missing(self):
        self.assertRaises(
            ValueError, ActionGroup, name=USER_INPUT_ACTION_GROUP_NAME, test=True
        )
