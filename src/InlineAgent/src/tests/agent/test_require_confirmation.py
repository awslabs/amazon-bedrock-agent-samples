# import unittest
import json
import unittest
from InlineAgent.agent.confirmation import require_confirmation
from InlineAgent.action_group import ActionGroups, ActionGroup
from InlineAgent.types import Executor


@require_confirmation
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


@require_confirmation
def get_lat_long_with_confirm(place: str) -> dict:
    """Returns the latitude and longitude for a given place name as a dict object of python.

    Args:
        place: City of the location
    """
    return json.dumps({"lat": 40.7128, "long": 74.0060})


@require_confirmation
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
        "requireConfirmation": "ENABLED",
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
        "requireConfirmation": "ENABLED",
    }
]


class TestRequireConfirm(unittest.TestCase):
    maxDiff = None

    def test___init___1(self):

        action_group = ActionGroup(
            name="WeatherActionGroup",
            description="Weather Action Group",
            tools=[get_current_weather],
            argument_key="Args:",
            test=True,
        )
        action_groups = ActionGroups(action_groups=[action_group]).actionGroups

        self.assertTrue(type(action_groups) is list)

        self.assertEqual(action_groups[0]["actionGroupName"], "WeatherActionGroup")

        self.assertEqual(
            action_groups[0]["actionGroupExecutor"]["customControl"],
            Executor.RETURN_CONTROL.value,
        )
        self.assertEqual(
            action_groups[0]["functionSchema"]["functions"], action_group_1_one_tool
        )

        self.assertCountEqual(
            action_groups[0]["functionSchema"]["functions"], action_group_1_one_tool
        )

    def test___init___2(self):
        tools = [get_current_weather, get_lat_long]

        action_group = ActionGroup(
            name="WeatherActionGroup",
            description="Weather Action Group",
            tools=tools,
            argument_key="Args:",
            test=True,
        )
        action_groups = ActionGroups(action_groups=[action_group]).actionGroups

        self.assertTrue(type(action_groups) is list)

        action_groups = action_groups[0]
        self.assertEqual(action_groups["actionGroupName"], "WeatherActionGroup")
        self.assertEqual(
            action_groups["actionGroupExecutor"]["customControl"],
            Executor.RETURN_CONTROL.value,
        )
        self.assertEqual(
            action_groups["functionSchema"]["functions"], action_group_1_two_tool
        )
        self.assertCountEqual(
            action_groups["functionSchema"]["functions"], action_group_1_two_tool
        )


if __name__ == "__main__":
    unittest.main()
