import json
import unittest
from InlineAgent.action_group import ActionGroup
from InlineAgent.agent.confirmation import require_confirmation
from InlineAgent.agent import InlineAgent


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


@require_confirmation
def get_lat_long_confirm(place: str) -> dict:
    """Returns the latitude and longitude for a given place name as a dict object of python.

    Args:
        place: City of the location
    """
    return json.dumps({"lat": 40.7128, "long": 74.0060})


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


data_test_weather_function = [
    {
        "actionGroupExecutor": {"customControl": "RETURN_CONTROL"},
        "functionSchema": {
            "functions": [
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
        },
        "actionGroupName": "WeatherActionGroup",
    }
]

data_test_location_function = [
    {
        "actionGroupExecutor": {"customControl": "RETURN_CONTROL"},
        "functionSchema": {
            "functions": [
                {
                    "name": "get_lat_long",
                    "description": "Returns the latitude and longitude for a given place name as a dict object of python.",
                    "parameters": {
                        "place": {
                            "type": "string",
                            "description": "City of the location",
                            "required": True,
                        }
                    },
                    "requireConfirmation": "DISABLED",
                },
            ]
        },
        "actionGroupName": "LocationActionGroup",
    }
]

data_test___init___1 = [
    {
        "actionGroupExecutor": {"customControl": "RETURN_CONTROL"},
        "functionSchema": {
            "functions": [
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
                        }
                    },
                    "requireConfirmation": "DISABLED",
                },
            ]
        },
        "actionGroupName": "WeatherActionGroup",
        "description": "This is action group to get weather",
    }
]

data_test___init___2 = [
    {
        "actionGroupExecutor": {"customControl": "RETURN_CONTROL"},
        "functionSchema": {
            "functions": [
                {
                    "name": "get_current_weather_confirm",
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
                    "requireConfirmation": "ENABLED",
                },
                {
                    "name": "get_lat_long",
                    "description": "Returns the latitude and longitude for a given place name as a dict object of python.",
                    "parameters": {
                        "place": {
                            "type": "string",
                            "description": "City of the location",
                            "required": True,
                        }
                    },
                    "requireConfirmation": "DISABLED",
                },
            ]
        },
        "actionGroupName": "WeatherActionGroup",
    }
]

data_test___init___3 = [
    {
        "actionGroupExecutor": {"customControl": "RETURN_CONTROL"},
        "functionSchema": {
            "functions": [
                {
                    "name": "get_current_weather_confirm",
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
                    "requireConfirmation": "ENABLED",
                },
                {
                    "name": "get_lat_long_confirm",
                    "description": "Returns the latitude and longitude for a given place name as a dict object of python.",
                    "parameters": {
                        "place": {
                            "type": "string",
                            "description": "City of the location",
                            "required": True,
                        }
                    },
                    "requireConfirmation": "ENABLED",
                },
            ]
        },
        "actionGroupName": "WeatherActionGroup",
    },
    {"parentActionGroupSignature": "AMAZON.UserInput", "actionGroupName": "UserInput"},
]


data_test___init___4 = [
    {
        "actionGroupExecutor": {"customControl": "RETURN_CONTROL"},
        "functionSchema": {
            "functions": [
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
                        }
                    },
                    "requireConfirmation": "DISABLED",
                },
            ]
        },
        "actionGroupName": "WeatherActionGroup",
    },
    {"parentActionGroupSignature": "AMAZON.UserInput", "actionGroupName": "UserInput"},
]

data_test___init___5 = [
    {"parentActionGroupSignature": "AMAZON.UserInput", "actionGroupName": "UserInput"}
]

data_test___init___6 = [
    {
        "actionGroupExecutor": {
            "lambda": "arn:aws:lambda:Mock-Region:Mock-Account:function:legal-doc-actions-xaqwa"
        },
        "functionSchema": {
            "functions": [
                {
                    "name": "save_doc_info",
                    "description": "call this action when you need to save information about the doc",
                    "parameters": {
                        "summary": {
                            "type": "string",
                            "description": "Summary of doc",
                            "required": True,
                        },
                        "author": {
                            "type": "string",
                            "description": "author of the doc",
                            "required": True,
                        },
                    },
                    "requireConfirmation": "ENABLED",
                }
            ]
        },
        "actionGroupName": "WeatherActionGroup",
    }
]

data_test___init___7 = [
    {
        "actionGroupExecutor": {
            "lambda": "arn:aws:lambda:Mock-Region:Mock-Account:function:legal-doc-actions-xaqwa"
        },
        "functionSchema": {
            "functions": [
                {
                    "name": "save_doc_info",
                    "description": "call this action when you need to save information about the doc",
                    "parameters": {
                        "summary": {
                            "type": "string",
                            "description": "Summary of doc",
                            "required": True,
                        },
                        "author": {
                            "type": "string",
                            "description": "author of the doc",
                            "required": True,
                        },
                    },
                    "requireConfirmation": "DISABLED",
                }
            ]
        },
        "actionGroupName": "WeatherActionGroup",
    }
]

data_test___init___8 = [
    {
        "parentActionGroupSignature": "AMAZON.CodeInterpreter",
        "actionGroupName": "CodeInterpreter",
    },
    {
        "parentActionGroupSignature": "ANTHROPIC.Computer",
        "parentActionGroupSignatureParams": {
            "type": "computer_20241022",
            "displayHeightPx": "768",
            "displayWidthPx": "1024",
            "displayNumber": "1",
        },
        "actionGroupName": "ComputerActionGroup",
    },
    {
        "parentActionGroupSignature": "ANTHROPIC.Bash",
        "parentActionGroupSignatureParams": {"type": "bash_20241022"},
        "actionGroupName": "BashActionGroup",
    },
    {"parentActionGroupSignature": "AMAZON.UserInput", "actionGroupName": "UserInput"},
]


class TestInlineAgent(unittest.TestCase):
    maxDiff = None

    def test___init___1(self):

        weather_action_group = ActionGroup(
            name="WeatherActionGroup",
            description="This is action group to get weather",
            tools=[get_current_weather, get_lat_long],
            argument_key="Args:",
            test=True,
        )
        agent = InlineAgent(
            foundation_model="MOCK_ID",
            instruction="You are a friendly assistant that is responsible for getting the current weather.",
            action_groups=[weather_action_group],
            user_input=False,
            agent_name="MockAgent",
        )

        self.assertEqual(len(agent.action_groups), 1)
        self.assertEqual(agent.action_groups, data_test___init___1)

    def test___init___2(self):
        weather_action_group = ActionGroup(
            name="WeatherActionGroup",
            tools=[get_current_weather_confirm, get_lat_long],
            argument_key="Args:",
            test=True,
        )
        agent = InlineAgent(
            foundation_model="MOCK_ID",
            instruction="You are a friendly assistant that is responsible for getting the current weather.",
            action_groups=[weather_action_group],
            user_input=False,
            agent_name="MockAgent",
        )

        self.assertEqual(agent.action_groups, data_test___init___2)

    def test___init___3(self):
        weather_action_group = ActionGroup(
            name="WeatherActionGroup",
            tools=[get_current_weather_confirm, get_lat_long_confirm],
            argument_key="Args:",
            test=True,
        )
        agent = InlineAgent(
            foundation_model="MOCK_ID",
            instruction="You are a friendly assistant that is responsible for getting the current weather.",
            action_groups=[
                weather_action_group,
            ],
            user_input=True,
            agent_name="MockAgent",
        )

        self.assertEqual(agent.action_groups, data_test___init___3)

    def test___init___4(self):
        weather_action_group = ActionGroup(
            name="WeatherActionGroup",
            tools=[get_current_weather, get_lat_long],
            argument_key="Args:",
            test=True,
        )
        agent = InlineAgent(
            foundation_model="MOCK_ID",
            instruction="You are a friendly assistant that is responsible for getting the current weather.",
            action_groups=[
                weather_action_group,
            ],
            user_input=True,
            agent_name="MockAgent",
        )

        self.assertEqual(agent.action_groups, data_test___init___4)

    def test___init___5(self):
        agent = InlineAgent(
            foundation_model="MOCK_ID",
            instruction="You are a friendly assistant that is responsible for getting the current weather.",
            user_input=True,
            agent_name="MockAgent",
        )

        self.assertEqual(agent.action_groups, data_test___init___5)

    def test___init___6(self):
        functions = [
            {
                "name": "save_doc_info",
                "description": "call this action when you need to save information about the doc",
                "parameters": {
                    "summary": {
                        "type": "string",
                        "description": "Summary of doc",
                        "required": True,
                    },
                    "author": {
                        "type": "string",
                        "description": "author of the doc",
                        "required": True,
                    },
                },
                "requireConfirmation": "ENABLED",
            }
        ]

        action_group = ActionGroup(
            name="WeatherActionGroup",
            lambda_name="legal-doc-actions-xaqwa",
            function_schema=functions,
            test=True,
        )
        agent = InlineAgent(
            foundation_model="MOCK_ID",
            instruction="You are a friendly assistant that is responsible for getting the current weather.",
            action_groups=[action_group],
            user_input=False,
            agent_name="MockAgent",
        )

        self.assertEqual(agent.action_groups, data_test___init___6)

    def test___init___7(self):
        functions = [
            {
                "name": "save_doc_info",
                "description": "call this action when you need to save information about the doc",
                "parameters": {
                    "summary": {
                        "type": "string",
                        "description": "Summary of doc",
                        "required": True,
                    },
                    "author": {
                        "type": "string",
                        "description": "author of the doc",
                        "required": True,
                    },
                },
                "requireConfirmation": "DISABLED",
            }
        ]
        action_group = ActionGroup(
            name="WeatherActionGroup",
            lambda_name="legal-doc-actions-xaqwa",
            function_schema=functions,
            test=True,
        )
        agent = InlineAgent(
            foundation_model="MOCK_ID",
            instruction="You are a friendly assistant that is responsible for getting the current weather.",
            action_groups=[action_group],
            user_input=False,
            agent_name="MockAgent",
        )

        self.assertEqual(agent.action_groups, data_test___init___7)

    def test___init___8(self):
        inbuiltTools = []

        computer_action_group = ActionGroup(
            name="ComputerActionGroup",
            argument_key="Args:",
            builtin_tools={
                "parentActionGroupSignature": "ANTHROPIC.Computer",
                "parentActionGroupSignatureParams": {
                    "type": "computer_20241022",
                    "displayHeightPx": "768",
                    "displayWidthPx": "1024",
                    "displayNumber": "1",
                },
            },
        )
        bash_action_group = ActionGroup(
            name="BashActionGroup",
            builtin_tools={
                "parentActionGroupSignature": "ANTHROPIC.Bash",
                "parentActionGroupSignatureParams": {
                    "type": "bash_20241022",
                },
            },
        )
        code_action_group = ActionGroup(
            name="CodeInterpreter",
            argument_key="Args:",
            builtin_tools={
                "parentActionGroupSignature": "AMAZON.CodeInterpreter",
            },
        )
        agent = InlineAgent(
            foundation_model="MOCK",
            instruction="You are an agent that helps draft and reviews legal documents, and provides document summaries.",
            action_groups=[code_action_group, computer_action_group, bash_action_group],
            user_input=True,
            agent_name="MockAgent",
        )

        self.assertEqual(agent.action_groups, data_test___init___8)


if __name__ == "__main__":
    unittest.main()
