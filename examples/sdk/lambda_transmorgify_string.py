from datetime import datetime, timedelta

today = datetime.today().strftime("%Y-%m-%d")
print(f"Today's date is: {today}")


def get_named_parameter(event, name):
    if "parameters" in event:
        return next(item for item in event["parameters"] if item["name"] == name)[
            "value"
        ]
    else:
        return None


def populate_function_response(event, response_body):
    return {
        "response": {
            "actionGroup": event["actionGroup"],
            "function": event["function"],
            "functionResponse": {
                "responseBody": {"TEXT": {"body": str(response_body)}}
            },
        }
    }


def transmorgify_string(input_string):
    return (
        input_string.replace("a", "o")
        .replace("e", "o")
        .replace("i", "o")
        .replace("u", "o")
    )


def lambda_handler(event, context):
    print(event)
    function = event["function"]
    if function == "transmorgify_string":
        input_string = get_named_parameter(event, "input_string")
        if not input_string:
            result = "Tool needs an input_string to transmorgify"
        result = transmorgify_string(input_string)
    else:
        result = f"Error, function '{function}' not recognized"

    response = populate_function_response(event, result)
    print(response)
    return response
