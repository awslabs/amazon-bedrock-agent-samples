import json
import unittest
from unittest.mock import Mock

import boto3
from requests import patch

from InlineAgent.action_group import ActionGroups, ActionGroup
from InlineAgent.constants import USER_INPUT_ACTION_GROUP_NAME
from InlineAgent.tools.mcp import MCPStdio


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


def get_lat_long(place: str) -> dict:
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

action_group_1_two_tool = [
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
    },
    {
        "name": "get_lat_long",
        "description": "Returns the latitude and longitude for a given place name as a dict object of python.",
        "parameters": {
            "place": {
                "type": "string",
                "description": "City of the location",
                "required": True,
            },
        },
        "requireConfirmation": "DISABLED",
    },
]

action_group_2_one_tool = [
    {
        "name": "web_search",
        "description": "Search a term in the public Internet. Useful for getting up to date information.",
        "parameters": {
            "search_term": {
                "type": "string",
                "description": "Term to search in the Internet",
                "required": True,
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

    def test_user_input(self):

        action_group = ActionGroup(
            name=USER_INPUT_ACTION_GROUP_NAME,
            builtin_tools={"parentActionGroupSignature": "AMAZON.UserInput"},
            test=True,
        )
        action_groups = ActionGroups(action_groups=[action_group])
        self.assertTrue(type(action_groups.actionGroups) is list)
        self.assertEqual(len(action_groups.actionGroups), 1)
        self.assertEqual(action_groups.tool_map, {})
        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupName"],
            USER_INPUT_ACTION_GROUP_NAME,
        )
        self.assertEqual(
            action_groups.actionGroups[0]["parentActionGroupSignature"],
            "AMAZON.UserInput",
        )
        self.assertEqual(
            action_groups.actionGroups[0],
            {
                "actionGroupName": "UserInput",
                "parentActionGroupSignature": "AMAZON.UserInput",
            },
        )

    def test_computer_use(self):

        computer_action_group = ActionGroup(
            name="Computer",
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

        text_action_group = ActionGroup(
            name="Text",
            builtin_tools={
                "parentActionGroupSignature": "ANTHROPIC.TextEditor",
                "parentActionGroupSignatureParams": {
                    "type": "text_editor_20250124",
                },
            },
            test=True,
        )

        bash_action_group = ActionGroup(
            name="Bash",
            builtin_tools={
                "parentActionGroupSignature": "ANTHROPIC.Bash",
                "parentActionGroupSignatureParams": {
                    "type": "bash_20250124",
                },
            },
            test=True,
        )
        action_groups = ActionGroups(
            action_groups=[computer_action_group, text_action_group, bash_action_group]
        )
        self.assertTrue(type(action_groups.actionGroups) is list)
        self.assertEqual(len(action_groups.actionGroups), 3)
        self.assertEqual(action_groups.tool_map, {})

        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupName"],
            "Computer",
        )
        self.assertEqual(
            action_groups.actionGroups[0]["parentActionGroupSignature"],
            "ANTHROPIC.Computer",
        )
        self.assertEqual(
            action_groups.actionGroups[0]["parentActionGroupSignatureParams"],
            {
                "type": "computer_20250124",
                "display_height_px": "768",
                "display_width_px": "1024",
                "display_number": "1",
            },
        )

        self.assertEqual(
            action_groups.actionGroups[1]["actionGroupName"],
            "Text",
        )
        self.assertEqual(
            action_groups.actionGroups[1]["parentActionGroupSignature"],
            "ANTHROPIC.TextEditor",
        )
        self.assertEqual(
            action_groups.actionGroups[1]["parentActionGroupSignatureParams"],
            {
                "type": "text_editor_20250124",
            },
        )

        self.assertEqual(
            action_groups.actionGroups[2]["actionGroupName"],
            "Bash",
        )
        self.assertEqual(
            action_groups.actionGroups[2]["parentActionGroupSignature"],
            "ANTHROPIC.Bash",
        )
        self.assertEqual(
            action_groups.actionGroups[2]["parentActionGroupSignatureParams"],
            {"type": "bash_20250124"},
        )

    def test_roc_one_tool(self):

        action_group = ActionGroup(
            name="Weather Action Group",
            tools=[get_current_weather],
            argument_key="Args:",
            test=True,
        )

        action_groups = ActionGroups(action_groups=[action_group])

        self.assertTrue(type(action_groups.actionGroups) is list)
        self.assertEqual(len(action_groups.actionGroups), 1)
        self.assertEqual(
            action_groups.tool_map, {get_current_weather.__name__: get_current_weather}
        )

        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupName"], "Weather Action Group"
        )
        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupExecutor"],
            {"customControl": "RETURN_CONTROL"},
        )
        self.assertEqual(
            action_groups.actionGroups[0]["functionSchema"]["functions"],
            action_group_1_one_tool,
        )

    def test_roc_one_tool_user_input(self):
        user_action_group = ActionGroup(
            name=USER_INPUT_ACTION_GROUP_NAME,
            builtin_tools={"parentActionGroupSignature": "AMAZON.UserInput"},
            test=True,
        )

        weather_action_group = ActionGroup(
            name="Weather Action Group",
            tools=[get_current_weather],
            argument_key="Args:",
            test=True,
        )

        action_groups = ActionGroups(
            action_groups=[user_action_group, weather_action_group]
        )

        self.assertTrue(type(action_groups.actionGroups) is list)
        self.assertEqual(len(action_groups.actionGroups), 2)
        self.assertEqual(
            action_groups.tool_map, {get_current_weather.__name__: get_current_weather}
        )
        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupName"],
            USER_INPUT_ACTION_GROUP_NAME,
        )
        self.assertEqual(
            action_groups.actionGroups[0]["parentActionGroupSignature"],
            "AMAZON.UserInput",
        )

        self.assertEqual(
            action_groups.actionGroups[1]["actionGroupName"], "Weather Action Group"
        )
        self.assertEqual(
            action_groups.actionGroups[1]["actionGroupExecutor"],
            {"customControl": "RETURN_CONTROL"},
        )
        self.assertEqual(
            action_groups.actionGroups[1]["functionSchema"]["functions"],
            action_group_1_one_tool,
        )

    def test_roc_one_action_action_group_two_tool(self):
        tools = {"FirstActionGroup": [get_current_weather, get_lat_long]}

        for name, tool in tools.items():
            weather_action_group = ActionGroup(
                name=name, tools=tool, argument_key="Args:", test=True
            )

            action_groups = ActionGroups(action_groups=[weather_action_group])

            self.assertTrue(type(action_groups.actionGroups) is list)
            self.assertEqual(len(action_groups.actionGroups), 1)
            self.assertEqual(
                action_groups.tool_map,
                {
                    get_current_weather.__name__: get_current_weather,
                    get_lat_long.__name__: get_lat_long,
                },
            )

            self.assertEqual(action_groups.actionGroups[0]["actionGroupName"], name)
            self.assertEqual(
                action_groups.actionGroups[0]["actionGroupExecutor"],
                {"customControl": "RETURN_CONTROL"},
            )
            self.assertEqual(
                action_groups.actionGroups[0]["functionSchema"]["functions"],
                action_group_1_two_tool,
            )

    def test_roc_two_action_action_group_two_tool(self):

        weather_action_group = ActionGroup(
            name="FirstActionGroup",
            tools=[get_current_weather, get_lat_long],
            argument_key="Args:",
            test=True,
        )

        web_search_action_group = ActionGroup(
            name="WebSearch", tools=[web_search], argument_key="Args:", test=True
        )

        action_groups = ActionGroups(
            action_groups=[weather_action_group, web_search_action_group]
        )

        self.assertTrue(type(action_groups.actionGroups) is list)
        self.assertEqual(len(action_groups.actionGroups), 2)
        self.assertEqual(
            action_groups.tool_map,
            {
                get_current_weather.__name__: get_current_weather,
                get_lat_long.__name__: get_lat_long,
                web_search.__name__: web_search,
            },
        )

        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupName"], "FirstActionGroup"
        )
        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupExecutor"],
            {"customControl": "RETURN_CONTROL"},
        )
        self.assertEqual(
            action_groups.actionGroups[0]["functionSchema"]["functions"],
            action_group_1_two_tool,
        )

        self.assertEqual(action_groups.actionGroups[1]["actionGroupName"], "WebSearch")
        self.assertEqual(
            action_groups.actionGroups[1]["actionGroupExecutor"],
            {"customControl": "RETURN_CONTROL"},
        )
        self.assertEqual(
            action_groups.actionGroups[1]["functionSchema"]["functions"],
            action_group_2_one_tool,
        )

    def test_lambda_one_tool(self):
        web_search_action_group = ActionGroup(
            name="WebSearch",
            lambda_name="Hello",
            function_schema=action_group_2_one_tool,
            test=True,
        )

        action_groups = ActionGroups(action_groups=[web_search_action_group])

        self.assertTrue(type(action_groups.actionGroups) is list)
        self.assertEqual(len(action_groups.actionGroups), 1)
        self.assertEqual(action_groups.tool_map, {})

        self.assertEqual(action_groups.actionGroups[0]["actionGroupName"], "WebSearch")
        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupExecutor"],
            {"lambda": "arn:aws:lambda:Mock-Region:Mock-Account:function:Hello"},
        )
        self.assertEqual(
            action_groups.actionGroups[0]["functionSchema"]["functions"],
            action_group_2_one_tool,
        )

    def test_lambda_user_input_one_tool(self):
        user_action_group = ActionGroup(
            name=USER_INPUT_ACTION_GROUP_NAME,
            builtin_tools={"parentActionGroupSignature": "AMAZON.UserInput"},
            test=True,
        )
        web_search_action_group = ActionGroup(
            name="WebSearch",
            lambda_name="web",
            function_schema=action_group_2_one_tool,
            test=True,
        )

        action_groups = ActionGroups(
            action_groups=[user_action_group, web_search_action_group]
        )

        self.assertTrue(type(action_groups.actionGroups) is list)
        self.assertEqual(len(action_groups.actionGroups), 2)
        self.assertEqual(action_groups.tool_map, {})

        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupName"],
            USER_INPUT_ACTION_GROUP_NAME,
        )
        self.assertEqual(
            action_groups.actionGroups[0]["parentActionGroupSignature"],
            "AMAZON.UserInput",
        )

        self.assertEqual(action_groups.actionGroups[1]["actionGroupName"], "WebSearch")
        self.assertEqual(
            action_groups.actionGroups[1]["actionGroupExecutor"],
            {"lambda": "arn:aws:lambda:Mock-Region:Mock-Account:function:web"},
        )
        self.assertEqual(
            action_groups.actionGroups[1]["functionSchema"]["functions"],
            action_group_2_one_tool,
        )

    def test_lambda_one_action_action_group_two_tool(self):

        action_group = ActionGroup(
            name="FirstActionGroup",
            lambda_name="first",
            function_schema=action_group_1_two_tool,
            test=True,
        )

        action_groups = ActionGroups(action_groups=[action_group])
        self.assertTrue(type(action_groups.actionGroups) is list)
        self.assertEqual(len(action_groups.actionGroups), 1)
        self.assertEqual(action_groups.tool_map, {})

        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupName"], "FirstActionGroup"
        )
        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupExecutor"],
            {"lambda": "arn:aws:lambda:Mock-Region:Mock-Account:function:first"},
        )
        self.assertEqual(
            action_groups.actionGroups[0]["functionSchema"]["functions"],
            action_group_1_two_tool,
        )

    def test_lambda_two_action_action_group_two_tool(self):

        weather_action_group = ActionGroup(
            name="FirstActionGroup",
            function_schema=action_group_1_two_tool,
            lambda_name="weather",
            test=True,
        )

        web_search_action_group = ActionGroup(
            name="WebSearch",
            function_schema=action_group_2_one_tool,
            lambda_name="web",
            test=True,
        )

        action_groups = ActionGroups(
            action_groups=[weather_action_group, web_search_action_group]
        )

        self.assertTrue(type(action_groups.actionGroups) is list)
        self.assertEqual(len(action_groups.actionGroups), 2)
        self.assertEqual(action_groups.tool_map, {})

        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupName"], "FirstActionGroup"
        )
        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupExecutor"],
            {"lambda": "arn:aws:lambda:Mock-Region:Mock-Account:function:weather"},
        )
        self.assertEqual(
            action_groups.actionGroups[0]["functionSchema"]["functions"],
            action_group_1_two_tool,
        )

        self.assertEqual(action_groups.actionGroups[1]["actionGroupName"], "WebSearch")
        self.assertEqual(
            action_groups.actionGroups[1]["actionGroupExecutor"],
            {"lambda": "arn:aws:lambda:Mock-Region:Mock-Account:function:web"},
        )
        self.assertEqual(
            action_groups.actionGroups[1]["functionSchema"]["functions"],
            action_group_2_one_tool,
        )

    def test_mcp_clients(self):
        self.mock_mcp_clients.callable_tools = {
            get_current_weather.__name__: get_current_weather,
            get_lat_long.__name__: get_lat_long,
        }
        self.mock_mcp_clients.function_schema = {"functions": action_group_1_two_tool}
        weather_action_group = ActionGroup(
            name="Weather Action Group", mcp_clients=[self.mock_mcp_clients], test=True
        )

        action_groups = ActionGroups(action_groups=[weather_action_group])

        self.assertTrue(type(action_groups.actionGroups) is list)
        self.assertEqual(len(action_groups.actionGroups), 1)
        self.assertEqual(
            action_groups.tool_map,
            {
                get_current_weather.__name__: get_current_weather,
                get_lat_long.__name__: get_lat_long,
            },
        )

        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupName"], "Weather Action Group"
        )
        self.assertEqual(
            action_groups.actionGroups[0]["actionGroupExecutor"],
            {"customControl": "RETURN_CONTROL"},
        )
        self.assertEqual(
            action_groups.actionGroups[0]["functionSchema"]["functions"],
            action_group_1_two_tool,
        )

    def test_multiple(self):
        user_action_group = ActionGroup(
            name=USER_INPUT_ACTION_GROUP_NAME,
            builtin_tools={"parentActionGroupSignature": "AMAZON.UserInput"},
            test=True,
        )
        lambda_web_search_action_group = ActionGroup(
            name="WebSearch",
            lambda_name="web",
            function_schema=action_group_2_one_tool,
            test=True,
        )

        self.mock_mcp_clients.callable_tools = {
            get_current_weather.__name__ + "mcp": get_current_weather,
            get_lat_long.__name__ + "mcp": get_lat_long,
        }
        self.mock_mcp_clients.function_schema = {"functions": action_group_1_two_tool}
        mcp_weather_action_group = ActionGroup(
            name="Weather Action Group", mcp_clients=[self.mock_mcp_clients], test=True
        )

        roc_weather_action_group = ActionGroup(
            name="FirstActionGroup",
            tools=[get_current_weather, get_lat_long],
            argument_key="Args:",
            test=True,
        )

        computer_action_group = ActionGroup(
            name="Computer",
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

        action_groups = ActionGroups(
            action_groups=[
                user_action_group,
                lambda_web_search_action_group,
                mcp_weather_action_group,
                roc_weather_action_group,
                computer_action_group,
            ]
        )

        self.assertTrue(type(action_groups.actionGroups) is list)
        self.assertEqual(len(action_groups.actionGroups), 5)
        self.assertEqual(
            action_groups.tool_map,
            {
                get_current_weather.__name__ + "mcp": get_current_weather,
                get_lat_long.__name__ + "mcp": get_lat_long,
                get_current_weather.__name__: get_current_weather,
                get_lat_long.__name__: get_lat_long,
            },
        )
