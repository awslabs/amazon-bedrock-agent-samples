import json


def get_named_parameter(event, name):
    return next(item for item in event["parameters"] if item["name"] == name)["value"]


def get_named_property(event, name):
    return next(
        item
        for item in event["requestBody"]["content"]["application/json"]["properties"]
        if item["name"] == name
    )["value"]


def create_success_response(event, payload):
    response_code = 200
    action_group = event["actionGroup"]
    api_path = event["apiPath"]

    response_body = {"application/json": {"body": json.dumps(payload)}}

    action_response = {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "apiPath": api_path,
            "httpMethod": event["httpMethod"],
            "httpStatusCode": response_code,
            "responseBody": response_body,
        },
    }

    return action_response


def create_success_function_response(event, payload):
    action_group = event["actionGroup"]
    function = event["function"]

    response_body = {"TEXT": {"body": json.dumps(payload)}}

    function_response = {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "function": function,
            "functionResponse": {
                "responseState": "REPROMPT",
                "responseBody": response_body,
            },
        },
    }

    return function_response


def create_error_response(event, errorString, code=500):
    response_code = code
    action_group = event["actionGroup"]
    api_path = event["apiPath"]
    payload = {"error": errorString}

    response_body = {"application/json": {"body": json.dumps(payload)}}

    action_response = {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "apiPath": api_path,
            "httpMethod": event["httpMethod"],
            "httpStatusCode": response_code,
            "responseBody": response_body,
        },
    }

    return action_response


def get_employee_time_off_balance():
    resp = {
        "remaining_balance": 10.25,
    }

    return resp


def create_employee_time_off_request(event):
    ndays = get_named_parameter(event, "number_of_days")
    sdate = get_named_parameter(event, "start_date")
    print(f"Got ndays: {ndays}, sdate: {sdate}")

    resp = {"start_date": sdate, "number_of_days": ndays, "id": 456}

    return resp


def lambda_handler(event, context):
    promptAttributes = None
    if "promptAttributes" in event:
        print(f"Got prompt details: {promptAttributes}")
        promptAttributes = event["promptAttributes"]

    actionGroup = event["actionGroup"]
    if actionGroup == "RequestTimeOff":
        print("Got action group: RequestTimeOff")
        return create_success_function_response(
            event, create_employee_time_off_request(event)
        )
    elif actionGroup == "GetTimeOff":
        print("Got action group: GetTimeOffBalance")
        return create_success_function_response(event, get_employee_time_off_balance())
    else:
        print(f"Unknown action group: {actionGroup}")
        return create_error_response(event, "Unknown action group", 400)
