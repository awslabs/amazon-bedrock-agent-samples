from typing import Any, Dict, Literal
import unittest

from InlineAgent.action_group import ActionGroupBuilder


def spider_run(website_url: str, mode: Literal["scrape", "crawl"] = "scrape"):
    """Execute the spider tool to scrape or crawl the specified website.

    Args:
        website_url (str): The URL to process. Must be a valid HTTP(S) URL.
        mode (Literal["scrape", "crawl"]): Operation mode.
            - "scrape": Extract content from single page
            - "crawl": Follow links and extract content from multiple pages

    Returns:
        Optional[str]: Extracted content in markdown format, or None if extraction fails
                    asnd log_failures is True.

    Raises:
        ValueError: If URL is invalid or missing, or if mode is invalid.
        ImportError: If spider-client package is not properly installed.
        ConnectionError: If network connection fails while accessing the URL.
        Exception: For other runtime errors.
    """

    return


spider_run_schema = {
    "name": "spider_run",
    "description": 'Execute the spider tool to scrape or crawl the specified website. Args: website_url (str): The URL to process. Must be a valid HTTP(S) URL. mode (Literal["scrape", "crawl"]): Operation mode. - "scrape": Extract content from single page - "crawl": Follow links and extract content from multiple pages Returns: Optional[str]: Extracted content in markdown format, or None if extraction fails asnd log_failures is True. Raises: ValueError: If URL is invalid or missing, or if mode is invalid. ImportError: If spider-client package is not properly installed. ConnectionError: If network connection fails while accessing the URL. Exception: For other runtime errors.',
    "parameters": {
        "website_url": {"type": "string", "description": "", "required": True},
        "mode": {"type": "string", "description": "", "required": False},
    },
    "requireConfirmation": "DISABLED",
}

spider_run_description = "Execute the spider tool to scrape or crawl the specified website. This function returns Optional[str]: Extracted content in markdown format, or None if extraction fails asnd log_failures is True. Raises: ValueError: If URL is invalid or missing, or if mode is invalid. ImportError: If spider-client package is not properly installed. ConnectionError: If network connection fails while accessing the URL. Exception: For other runtime errors."

spider_run_param = {
    "website_url": "str The URL to process. Must be a valid HTTP(S) URL.",
    "mode": 'Literal["scrape", "crawl"] Operation mode. - "scrape": Extract content from single page - "crawl": Follow links and extract content from multiple pages',
}


def no_docstring():
    pass


def invalid_docstring():
    """"""
    pass


def invalid_docstring2():
    """This is a docstring

    Parameters:
    """
    pass


def invalid_docstring3():
    """This is a docstring

    Parameters:
        hello: This is a mock

    Returns:
    """
    pass


def get_current_weather(location: str, state: str, unit: str = "fahrenheit") -> dict:
    """Get the current weather in a given location.

    Args:
        location: The city, e.g., San Francisco
        state: The state eg CA
        unit: The unit to use, e.g., fahrenheit or celsius. Defaults to "fahrenheit"
    """
    # Replace with actual API call or data retrieval
    pass


get_current_weather_description = "Get the current weather in a given location."
get_current_weather_params = {
    "location": "The city, e.g., San Francisco",
    "state": "The state eg CA",
    "unit": 'The unit to use, e.g., fahrenheit or celsius. Defaults to "fahrenheit"',
}


async def get_lat_long(place: str) -> dict:
    """

    Returns the latitude and longitude for a given place name as a dict object of python.

    Args:
        place: City of the location
    """
    pass


get_lat_long_description = "Returns the latitude and longitude for a given place name as a dict object of python."

get_lat_long_args = {"place": "City of the location"}


class GitHubAPIWrapper:
    def __init__(self):
        pass

    def get_issue(self, issue_number: int) -> Dict[str, Any]:
        """
        Fetches a specific issue and its first 10 comments
        Parameters:
            issue_number(int): The number for the github issue
        Returns:
            dict: A dictionary containing the issue's title,
            body, comments as a string, and the username of the user
            who opened the issue
        """
        pass

    get_issue_description = "Fetches a specific issue and its first 10 comments This function returns dict: A dictionary containing the issue's title, body, comments as a string, and the username of the user who opened the issue"
    get_issue_params = {"issue_number": "int The number for the github issue"}

    def list_files_in_bot_branch(self) -> str:
        """
        Fetches all files in the active branch of the repo,
        the branch the bot uses to make changes.
        Returns:
            str: A plaintext list containing the filepaths in the branch.
        """
        pass

    list_files_in_bot_branch_description = "Fetches all files in the active branch of the repo, the branch the bot uses to make changes. Returns: str: A plaintext list containing the filepaths in the branch."
    list_files_in_bot_branch_params = {}


check_indent_level = """
        website_url (str): The URL to process. Must be a valid HTTP(S) URL.
        mode (Literal["scrape", "crawl"]): Operation mode.
            - "scrape": Extract content from single page
            - "crawl": Follow links and extract content from multiple pages
"""


class TestActionGroupBuilder(unittest.TestCase):
    maxDiff = None

    def test_parse_docstring_invalid_docstring_1(self):
        self.assertRaises(
            ValueError, ActionGroupBuilder.parse_docstring, invalid_docstring.__doc__
        )

    def test_parse_docstring_invalid_docstring_2(self):
        description, param_descriptions = ActionGroupBuilder.parse_docstring(
            invalid_docstring2.__doc__
        )
        self.assertEqual(description, "This is a docstring")
        self.assertEqual(param_descriptions, {})

    def test_parse_docstring_invalid_docstring_3(self):
        description, param_descriptions = ActionGroupBuilder.parse_docstring(
            invalid_docstring3.__doc__
        )
        self.assertEqual(description, "This is a docstring")
        self.assertEqual(param_descriptions, {"hello": "This is a mock"})

    def test_parse_docstring_spider_run(self):
        description, param_descriptions = ActionGroupBuilder.parse_docstring(
            spider_run.__doc__, argument_key="Args:"
        )

        self.assertEqual(description, spider_run_description)
        self.assertEqual(param_descriptions, spider_run_param)

    def test_parse_docstring_get_current_weather(self):
        description, param_descriptions = ActionGroupBuilder.parse_docstring(
            get_current_weather.__doc__, argument_key="Args:"
        )
        self.assertEqual(description, get_current_weather_description)
        self.assertEqual(param_descriptions, get_current_weather_params)

    def test_parse_docstring_get_lat_long(self):
        description, param_descriptions = ActionGroupBuilder.parse_docstring(
            get_lat_long.__doc__, argument_key="Args:"
        )
        self.assertEqual(description, get_lat_long_description)
        self.assertEqual(param_descriptions, get_lat_long_args)

    def test_parse_docstring_github_APIWrapper(self):

        tools = [GitHubAPIWrapper.get_issue, GitHubAPIWrapper.list_files_in_bot_branch]

        description, param_descriptions = ActionGroupBuilder.parse_docstring(
            tools[0].__doc__
        )
        self.assertEqual(description, GitHubAPIWrapper.get_issue_description)
        self.assertEqual(param_descriptions, GitHubAPIWrapper.get_issue_params)

        description, param_descriptions = ActionGroupBuilder.parse_docstring(
            tools[1].__doc__
        )
        self.assertEqual(
            description, GitHubAPIWrapper.list_files_in_bot_branch_description
        )
        self.assertEqual(
            param_descriptions, GitHubAPIWrapper.list_files_in_bot_branch_params
        )

    def test_get_indent_level(self):

        level = [0, 8, 8, 12, 12, 0]
        for idx, line in enumerate(check_indent_level.split("\n")):
            self.assertEqual(ActionGroupBuilder.get_indent_level(line), level[idx])

    def test_get_new_param_invalid_docstring(self):
        self.assertRaises(ValueError, ActionGroupBuilder.get_new_param, "")

        self.assertRaises(ValueError, ActionGroupBuilder.get_new_param, "hello")

        self.assertRaises(ValueError, ActionGroupBuilder.get_new_param, "hello:")

    def test_get_new_param(self):

        current_param, current_desc = ActionGroupBuilder.get_new_param(
            "issue_number(int): The number for the github issue"
        )

        self.assertEqual(current_param, "issue_number")
        self.assertEqual(current_desc, ["int The number for the github issue"])

        current_param, current_desc = ActionGroupBuilder.get_new_param(
            "     issue_number     (int)     :      The number for the github issue           "
        )

        self.assertEqual(current_param, "issue_number")
        self.assertEqual(current_desc, ["int The number for the github issue"])

    def test_clean_string(self):

        self.assertEqual(
            ActionGroupBuilder.clean_string(
                "     issue_number     (int)     :      The number for the github issue           "
            ),
            " issue_number (int) : The number for the github issue",
        )

    def test__map_python_type_to_schema_type(self):
        self.assertEqual(
            ActionGroupBuilder._map_python_type_to_schema_type("str"), "string"
        )
        self.assertEqual(
            ActionGroupBuilder._map_python_type_to_schema_type("int"), "integer"
        )
        self.assertEqual(
            ActionGroupBuilder._map_python_type_to_schema_type("float"), "number"
        )
        self.assertEqual(
            ActionGroupBuilder._map_python_type_to_schema_type("bool"), "boolean"
        )
        self.assertEqual(
            ActionGroupBuilder._map_python_type_to_schema_type("list"), "array"
        )
        self.assertEqual(
            ActionGroupBuilder._map_python_type_to_schema_type("Dict"), "string"
        )
        self.assertEqual(
            ActionGroupBuilder._map_python_type_to_schema_type("Any"), "string"
        )
        self.assertEqual(
            ActionGroupBuilder._map_python_type_to_schema_type("Literal"), "string"
        )

    def test_no_docstring(self):
        self.assertRaises(
            ValueError, ActionGroupBuilder.create_function_schema, no_docstring
        )

    def test_create_function(self):
        self.assertEqual(
            ActionGroupBuilder.create_function_schema(spider_run), spider_run_schema
        )
