import os
import json
import uuid
import boto3

from boto3.dynamodb.conditions import Key, Attr

dynamodb_resource = boto3.resource("dynamodb")
dynamodb_table = os.getenv("dynamodb_table")
dynamodb_pk = os.getenv("dynamodb_pk")
dynamodb_sk = os.getenv("dynamodb_sk")


def get_named_parameter(event, name):
    try:
        return next(item for item in event["parameters"] if item["name"] == name)[
            "value"
        ]
    except:
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


def put_dynamodb(table_name, item):
    table = dynamodb_resource.Table(table_name)
    resp = table.put_item(Item=item)
    return resp


def read_dynamodb(
    table_name: str,
    pk_field: str,
    pk_value: str,
    sk_field: str = None,
    sk_value: str = None,
):
    try:
        table = dynamodb_resource.Table(table_name)
        # Create expression
        if sk_value:
            key_expression = Key(pk_field).eq(pk_value) & Key(sk_field).begins_with(
                sk_value
            )
        else:
            key_expression = Key(pk_field).eq(pk_value)

        query_data = table.query(KeyConditionExpression=key_expression)

        return query_data["Items"]
    except Exception:
        print(f"Error querying table: {table_name}.")


def open_ticket(customer_id, msg):
    ticket_id = str(uuid.uuid1())
    item = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "description": msg,
        "status": "created",
    }
    resp = put_dynamodb(dynamodb_table, item)
    print(resp)
    return "Thanks for contact customer {}! Your support case was generated with ID: {}".format(
        customer_id, ticket_id
    )


def get_ticket_status(customer_id, ticket_id: str = None):
    return read_dynamodb(
        dynamodb_table, dynamodb_pk, customer_id, dynamodb_sk, ticket_id
    )


def lambda_handler(event, context):
    print(event)

    # name of the function that should be invoked
    function = event.get("function", "")

    # parameters to invoke function with
    parameters = event.get("parameters", [])
    customer_id = get_named_parameter(event, "customer_id")

    if function == "open_ticket":
        msg = get_named_parameter(event, "msg")
        result = open_ticket(customer_id, msg)
    elif function == "get_ticket_status":
        ticket_id = get_named_parameter(event, "ticket_id")
        result = get_ticket_status(customer_id, ticket_id)
    else:
        result = f"Error, function '{function}' not recognized"

    response = populate_function_response(event, result)
    print(response)
    return response
