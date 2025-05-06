import boto3
import json
import os
import psycopg2
import uuid
from botocore.exceptions import ClientError
from decimal import Decimal
from datetime import date, datetime

SECRET_NAME = os.environ["SECRET_NAME"]
POSTGRESQL_HOST = os.environ["POSTGRESQL_HOST"]
DATABASE_NAME = os.environ["DATABASE_NAME"]
QUESTION_ANSWERS_TABLE = os.environ["QUESTION_ANSWERS_TABLE"]
AWS_REGION = os.environ["AWS_REGION"]

FILE_TABLES_INFORMATION = "tables_information.txt"

def get_secret(secret_name, region_name):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e
    secret = json.loads(get_secret_value_response["SecretString"])
    print(secret)
    return secret


def get_postgresql_connection():
    secret = get_secret(SECRET_NAME, AWS_REGION)
    try:
        conn = psycopg2.connect(
            host=POSTGRESQL_HOST,
            database=DATABASE_NAME,
            user=secret["username"],
            password=secret["password"],
        )
        print("Connected to the PostgreSQL database!")
    except (Exception, psycopg2.Error) as error:
        print("Error connecting to the PostgreSQL database:", error)
        return False
    return conn


def get_size(string):
    return len(string.encode("utf-8"))


def get_query_results(sql_query):
    connection = get_postgresql_connection()
    if connection == False:
        return {
            "error": "Something went wrong connecting to the database, ask the user to try again later."
        }

    message = ""
    cur = connection.cursor()
    records = []
    records_to_return = []
    # Execute a SQL query
    try:
        cur.execute(sql_query)
        rows = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]
        for item in rows:
            record = {}
            for x, value in enumerate(item):
                if type(value) is Decimal:
                    record[column_names[x]] = float(value)
                elif isinstance(value, date):
                    record[column_names[x]] = str(value)
                else:
                    record[column_names[x]] = value
            records.append(record)
        if get_size(json.dumps(records)) > 24000:

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
        else:
            records_to_return = records

    except (Exception, psycopg2.Error) as error:
        print("Error executing SQL query:", error)
        connection.rollback()  # Rollback the transaction if there's an error
        return {"error": error.pgerror}
    # Close the cursor and the connection
    ##cur.close()
    # conn.close()
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
                dynamodb_client = boto3.client("dynamodb")
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
