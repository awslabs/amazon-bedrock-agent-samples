import json
import inspect
from typing import Any, Dict


def get_named_parameter(event: Dict[str, Any], name: str) -> Any:
    """Extract a named parameter from the event object."""
    if "parameters" in event:
        return next(item for item in event["parameters"] if item["name"] == name)[
            "value"
        ]
    else:
        return None


def populate_function_response(
    event: Dict[str, Any], response_body: Any
) -> Dict[str, Any]:
    """Create the response structure expected by the agent."""
    return {
        "response": {
            "actionGroup": event["actionGroup"],
            "function": event["function"],
            "functionResponse": {
                "responseBody": {"TEXT": {"body": str(response_body)}}
            },
        }
    }


def lookup_user_profile(input_string: str) -> str:
    """Look up a user profile by ID."""
    # Actually just returns canned data
    if "1234" in input_string:
        return json.dumps(
            {"name": "John Doe", "age": 30, "email": "john.doe@example.com"}
        )
    else:
        return json.dumps({"error": "No user with that ID was found"})


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler that wraps the main function.
    Extracts parameters from the event and formats the response.
    """
    print(f"Received event: {event}")

    function = event["function"]
    if function == "lookup_user_profile":
        # Get parameters from the event
        params = {}
        for param_name in inspect.signature(lookup_user_profile).parameters:
            param_value = get_named_parameter(event, param_name)
            if param_value is None:
                # Check session state if parameter not found
                session_state = event.get("sessionAttributes", {})
                if session_state and param_name in session_state:
                    param_value = session_state[param_name]
                else:
                    result = f"Missing required parameter: {param_name}"
                    return populate_function_response(event, result)
            params[param_name] = param_value

        try:
            # Call the function with extracted parameters
            result = lookup_user_profile(**params)
            return populate_function_response(event, result)
        except Exception as e:
            error_message = f"Error executing lookup_user_profile: {str(e)}"
            print(error_message)
            return populate_function_response(event, error_message)
    else:
        result = f"Error: Function '{function}' not recognized"
        return populate_function_response(event, result)
