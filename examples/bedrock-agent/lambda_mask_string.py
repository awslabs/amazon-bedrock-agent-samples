import json
import inspect
from typing import Any, Dict

def get_named_parameter(event: Dict[str, Any], name: str) -> Any:
    """Extract a named parameter from the event object."""
    if 'parameters' in event:
        return next(item for item in event['parameters'] if item['name'] == name)['value']
    else:
        return None

def populate_function_response(event: Dict[str, Any], response_body: Any) -> Dict[str, Any]:
    """Create the response structure expected by the agent."""
    return {
        'response': {
            'actionGroup': event['actionGroup'],
            'function': event['function'],
            'functionResponse': {
                'responseBody': {
                    'TEXT': {'body': str(response_body)}
                }
            }
        }
    }

def mask_string(input_string: str) -> str:
    """Masks a string by replacing all but the last four characters with asterisks."""
    if len(input_string) <= 4:
        return input_string
    else:
        return "*" * (len(input_string) - 4) + input_string[-4:]


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler that wraps the main function.
    Extracts parameters from the event and formats the response.
    """
    print(f"Received event: {event}")

    function = event['function']
    if function == 'mask_string':
        # Get parameters from the event
        params = {}
        for param_name in inspect.signature(mask_string).parameters:
            param_value = get_named_parameter(event, param_name)
            if param_value is None:
                # Check session state if parameter not found
                session_state = event.get('sessionAttributes', {})
                if session_state and param_name in session_state:
                    param_value = session_state[param_name]
                else:
                    result = f"Missing required parameter: {param_name}"
                    return populate_function_response(event, result)
            params[param_name] = param_value

        try:
            # Call the function with extracted parameters
            result = mask_string(**params)
            return populate_function_response(event, result)
        except Exception as e:
            error_message = f"Error executing mask_string: {str(e)}"
            print(error_message)
            return populate_function_response(event, error_message)
    else:
        result = f"Error: Function '{function}' not recognized"
        return populate_function_response(event, result)