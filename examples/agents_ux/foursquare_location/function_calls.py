import inspect
from functools import wraps
from typing import Optional, Dict, Any

# Store decorated functions
_decorated_functions = []


def bedrock_agent_tool(action_group: Optional[str] = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Store the function and its metadata
        func._action_group = action_group
        _decorated_functions.append(func)
        return wrapper

    return decorator


def parse_docstring(docstring: Optional[str]) -> tuple[str, Dict[str, str]]:
    """Parse a docstring to extract function description and parameter descriptions."""
    if not docstring:
        return "", {}

    # Split docstring into description and args sections
    parts = docstring.split("Args:")

    # Get function description
    description = parts[0].strip()

    # Parse parameter descriptions if they exist
    param_descriptions = {}
    if len(parts) > 1:
        param_section = parts[1].strip()
        # Split parameters into lines and parse each
        param_lines = param_section.split("\n")
        current_param = None
        current_desc = []

        for line in param_lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a new parameter
            if not line.startswith(" "):
                # Save the previous parameter if it exists
                if current_param:
                    param_descriptions[current_param] = " ".join(current_desc).strip()
                    current_desc = []

                # Parse new parameter
                param_parts = line.split(":", 1)
                if len(param_parts) == 2:
                    current_param = param_parts[0].strip()
                    current_desc = [param_parts[1].strip()]
            else:
                # Continue previous parameter description
                if current_param:
                    current_desc.append(line.strip())

        # Save the last parameter
        if current_param:
            param_descriptions[current_param] = " ".join(current_desc).strip()

    return description, param_descriptions


def _map_python_type_to_schema_type(python_type: str) -> str:
    """Map Python type names to JSON schema type names."""
    type_mapping = {
        'str': 'string',
        'int': 'integer',
        'float': 'number',
        'bool': 'boolean',
        'list': 'array',
        'dict': 'object',  # though not in allowed list, included for completeness
    }
    return type_mapping.get(python_type, 'string')  # default to string for unknown types


def get_bedrock_tools(include_callable=True):
    tools = []
    for func in _decorated_functions:
        # Get function signature
        sig = inspect.signature(func)

        # Parse docstring
        description, param_descriptions = parse_docstring(func.__doc__)

        # Build parameters list with descriptions
        parameters = []
        for name, param in sig.parameters.items():
            # Get the Python type name and map it to schema type
            python_type = (param.annotation.__name__
                           if param.annotation != inspect.Parameter.empty
                           else 'any')
            schema_type = _map_python_type_to_schema_type(python_type)

            param_info = {
                'name': name,
                'type': schema_type,
                'description': param_descriptions.get(name, ''),
                'required': param.default == inspect.Parameter.empty
            }
            parameters.append(param_info)

        tool_info = {
            'function': func.__name__,
            'description': description,
            'parameters': parameters,
            'action_group': getattr(func, '_action_group', None)  # Get action_group if it exists
        }

        if include_callable:
            tool_info['callable'] = func
        tools.append(tool_info)

    return tools


def invoke_tool(function_to_call: dict):
    tools = get_bedrock_tools()
    for tool in tools:
        if tool['function'] == function_to_call['function']:
            return tool['callable'](**function_to_call['parameters']), None

    return None, f"Error no function exists by name {function_to_call['function']}"


def convert_tools_to_function_schema(tools: list) -> list:
    """
    Convert tools metadata to function schema format, grouped by action groups.

    Args:
        tools: List of tool metadata from get_bedrock_tools()
    Returns:
        list: List of action group schemas, each containing function schemas
    """
    # First convert tools to base function schemas
    converted_functions = []
    for tool in tools:
        # Convert parameters to required format
        parameters = {}
        for param in tool['parameters']:
            # Convert type name to lowercase as expected in schema
            param_type = param['type'].lower()
            # Handle 'any' type as string by default
            if param_type == 'any':
                param_type = 'string'

            parameters[param['name']] = {
                'type': param_type,
                'description': param['description'],
                'required': param['required']
            }

        # Create function schema without actionGroupName
        function_data = {
            'name': tool['function'],
            'description': tool['description'],
            'parameters': parameters
        }
        # Store with action group for grouping, but don't include in final function schema
        converted_functions.append((tool.get('action_group'), function_data))

    # Group functions by action group
    action_groups = {}
    for action_group, func_data in converted_functions:
        if action_group:
            if action_group not in action_groups:
                action_groups[action_group] = []
            action_groups[action_group].append(func_data)

    # Create final schema structure
    result = []
    for action_group, functions in action_groups.items():
        schema = {
            'actionGroupName': action_group,
            'actionGroupExecutor': {'customControl': 'RETURN_CONTROL'},
            'functionSchema': {
                'functions': functions
            }
        }
        result.append(schema)

    return result

def parse_function_parameters(data):
    """
    Recursively parse a dictionary to extract function invocation parameters.
    Returns a dictionary of parameter name-value pairs.

    Args:
        data (dict or list): The input data structure to parse

    Returns:
        dict: A dictionary mapping parameter names to their values
    """
    function_to_call = {}
    function_to_call['invocationId'] = data['invocationId']

    def recursive_extract(obj):
        if isinstance(obj, dict):
            # Check if we've found a functionInvocationInput
            if 'functionInvocationInput' in obj:
                func_input = obj['functionInvocationInput']
                # Extract function metadata
                function_to_call['actionGroup'] = func_input.get('actionGroup')
                function_to_call['function'] = func_input.get('function')
                function_to_call['agentId'] = func_input.get('agentId')
                function_to_call['parameters'] = {}
                # Process parameters list if it exists
                if 'parameters' in func_input:
                    for param in func_input['parameters']:
                        if all(key in param for key in ['name', 'value']):
                            function_to_call['parameters'][param['name']] = param['value']

            # Continue searching through all dictionary values
            for value in obj.values():
                recursive_extract(value)

        elif isinstance(obj, list):
            # Search through all list items
            for item in obj:
                recursive_extract(item)

    recursive_extract(data)
    return function_to_call


if __name__ == "__main__":
    # Example usage
    input_data = {
        'invocationId': 'cd6f2da5-49e8-4660-a21f-cbeb3bac9f76',
        'invocationInputs': [{
            'functionInvocationInput': {
                'actionGroup': 'StockPriceTool',
                'actionInvocationType': 'RESULT',
                'agentId': 'INLINE_AGENT',
                'function': 'get_stock_price',
                'parameters': [
                    {'name': 'end_date', 'type': 'string', 'value': '20241207'},
                    {'name': 'symbol', 'type': 'string', 'value': 'SPY'},
                    {'name': 'start_date', 'type': 'string', 'value': '20241207'}
                ]
            }
        }]
    }
    # Parse and print results
    result = parse_function_parameters(input_data)
    print("Extracted parameters:")
    for key, value in result.items():
        print(f"{key}: {value}")