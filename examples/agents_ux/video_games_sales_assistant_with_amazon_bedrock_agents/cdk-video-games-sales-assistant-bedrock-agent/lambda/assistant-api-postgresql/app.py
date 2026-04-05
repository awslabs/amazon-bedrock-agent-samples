import boto3
import json
import os
import uuid
from decimal import Decimal
from datetime import datetime

CLUSTER_ARN = os.environ["CLUSTER_ARN"]
SECRET_ARN = os.environ["SECRET_ARN"]
DATABASE_NAME = os.environ["DATABASE_NAME"]
QUESTION_ANSWERS_TABLE = os.environ["QUESTION_ANSWERS_TABLE"]

FILE_TABLES_INFORMATION = "tables_information.txt"

rds_data_client = boto3.client("rds-data")
dynamodb_client = boto3.client("dynamodb")


def get_size(string):
    return len(string.encode("utf-8"))


def parse_rds_data_response(response):
    """Parse RDS Data API response into a list of dicts."""
    columns = [col["name"] for col in response.get("columnMetadata", [])]
    records = []
    for row in response.get("records", []):
        record = {}
        for i, field in enumerate(row):
            if "isNull" in field and field["isNull"]:
                record[columns[i]] = None
            elif "stringValue" in field:
                record[columns[i]] = field["stringValue"]
            elif "longValue" in field:
                record[columns[i]] = field["longValue"]
            elif "doubleValue" in field:
                record[columns[i]] = field["doubleValue"]
            elif "booleanValue" in field:
                record[columns[i]] = field["booleanValue"]
            else:
                record[columns[i]] = str(field)
        records.append(record)
    return records


def get_query_results(sql_query):
    """Execute a SQL query using the RDS Data API and return results."""
    message = ""
    try:
        response = rds_data_client.execute_statement(
            resourceArn=CLUSTER_ARN,
            secretArn=SECRET_ARN,
            database=DATABASE_NAME,
            sql=sql_query,
            includeResultMetadata=True,
        )
        records = parse_rds_data_response(response)

        records_to_return = records
        if get_size(json.dumps(records)) > 24000:
            records_to_return = []
            for item in records:
                if get_size(json.dumps(records_to_return)) <= 24000:
                    records_to_return.append(item)
            message = (
                "The data is too large, it has been truncated from "
                + str(len(records))
                + " to "
                + str(len(records_to_return))
                + " rows."
            )

    except Exception as error:
        print("Error executing SQL query:", error)
        return {"error": str(error)}

    if message != "":
        return {"result": records_to_return, "message": message}
    else:
        return {"result": records_to_return}


def lambda_handler(event, context):
    print(event)
    action_group = event.get("actionGroup")
    api_path = event.get("apiPath")
    user_question = event.get("inputText")
    promptSessionAttributes = event.get("promptSessionAttributes", {})

    if "queryUuid" in promptSessionAttributes:
        query_uuid = promptSessionAttributes["queryUuid"]
    else:
        query_uuid = str(uuid.uuid4())

    print("api_path: ", api_path)

    result = ""
    response_code = 200

    if api_path == "/runSQLQuery":
        # Retrieve query results to respond to the user's questions
        sql_query = ""
        for item in event["requestBody"]["content"]["application/json"]["properties"]:
            if item["name"] == "SQLQuery":
                sql_query = item["value"]

        print("*---------*")
        print(sql_query)
        print("*---------*")

        if sql_query != "":
            data = get_query_results(sql_query)
            print("---------")
            print(data)
            print("---------")
            if "error" in data:
                result = data
            else:
                try:
                    response = dynamodb_client.put_item(
                        TableName=QUESTION_ANSWERS_TABLE,
                        Item={
                            "id": {"S": query_uuid},
                            "my_timestamp": {"N": str(int(datetime.now().timestamp()))},
                            "datetime": {"S": str(datetime.now())},
                            "question": {"S": user_question},
                            "query": {"S": sql_query},
                            "data": {"S": json.dumps(data)},
                        },
                    )
                except:
                    print("Error writing the answer in dynamodb")
                    result = {"data": data, "message": "Data results were not stored"}
                result = {"data": data}
        else:
            result = {"message": "No SQL query provided to execute"}

    elif api_path == "/getCurrentDate":
        # Return the current date in YYYY/MM/DD format
        current_date = datetime.now().strftime("%Y/%m/%d")
        result = {"currentDate": current_date}

    elif api_path == "/getTablesInformation":
        # Provide information about the video game sales database
        try:
            with open(FILE_TABLES_INFORMATION, "r") as file:
                tables_info = file.read()
            result = {"tablesInformation": tables_info}
        except FileNotFoundError:
            result = {"error": "Tables information file not found"}
        except Exception as e:
            result = {"error": f"Error loading tables information: {str(e)}"}

    else:
        response_code = 404
        result = {"error": f"Unrecognized api path: {action_group}::{api_path}"}

    response_body = {"application/json": {"body": result}}

    action_response = {
        "actionGroup": action_group,
        "apiPath": api_path,
        "httpMethod": event.get("httpMethod"),
        "httpStatusCode": response_code,
        "responseBody": response_body,
    }

    api_response = {"messageVersion": "1.0", "response": action_response}

    print(get_size(json.dumps(api_response)))

    return api_response
