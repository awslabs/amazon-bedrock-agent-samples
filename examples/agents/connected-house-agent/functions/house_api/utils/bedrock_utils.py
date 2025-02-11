import json
import boto3
import os


MODEL_ID = os.environ["MODEL_ID"]

bedrock_client = boto3.client(
    "bedrock-runtime", region_name=os.environ.get("AWS_REGION")
)


def invoke_bedrock_model(model_id, message_list, inf_params=None):
    if inf_params is None:
        inf_params = {
            "max_new_tokens": 500,
            "top_p": 0.1,
            "top_k": 20,
            "temperature": 0,
        }

    request = {
        "schemaVersion": "messages-v1",
        "messages": message_list,
        "inferenceConfig": inf_params,
    }

    response = bedrock_client.invoke_model(
        modelId=model_id,
        body=json.dumps(request),
    )

    response_body = json.loads(response["body"].read())
    return response_body["output"]["message"]["content"][0]["text"]


def analyze_camera_image(base64_string, camera_location, question):

    prompt = f"""
    You are analysing images from a home surveillance camera monitoring the {camera_location}
    Your answer is going to be used by another genai agent that queries different devices in a connected home, 
    so formulate your answer as if reporting from the camera.

    Given the image above, answer this question concisely: {question}"""

    message_list = [
        {
            "role": "user",
            "content": [
                {"image": {"format": "jpeg", "source": {"bytes": base64_string}}},
                {"text": prompt},
            ],
        }
    ]

    try:
        return invoke_bedrock_model(MODEL_ID, message_list)
    except Exception as e:
        if "ThrottlingException" in str(e):
            return (
                "The request to analyse the image got throttled. You must wait a bit :("
            )
        raise


def analyze_camera_history(history, question):
    prompt = f"""
    ## Instructions
    You are a home automation tool, that analyses a log from a camera.
    The logs are generated continuously with description about what the camera observes, 
    and your job is to effetively answer the provided question given that history.

    Consider all available information, including the description and the timestamps in the data,
    and provide a comprehensive and thorough response to the question below.

    ## History
    {history}

    ## Question
    {question}

    ## Rules
    - Don't mention that you analysing a log. Only consider content of it.
    - If the history is empty, state that there's not logs from the specified time range
    - You MUST Only include information that's in the logs. Do NOT make up any information

    Given the above history, answer the question thoroughly.
    """

    message_list = [
        {
            "role": "user",
            "content": [
                {"text": prompt},
            ],
        }
    ]

    inf_params = {
        "max_new_tokens": 700,
        "top_p": 0.1,
        "top_k": 20,
        "temperature": 0,
    }

    try:
        return invoke_bedrock_model(MODEL_ID, message_list, inf_params=inf_params)
    except Exception as e:
        if "ThrottlingException" in str(e):
            return "The request to analyse the history got throttled. Either try a shorter time range, or wait a bit"
        raise


def generate_sql_query(camera_location, timestamp_start, timestamp_end, table_name):
    sample_queries = get_sample_queries(camera_location, table_name)

    get_sql_prompt = f"""
    ## Instructions
    You are an expert developer and data engineer. Given a table indexed in Glue, 
    with the data in S3 with the schema below, you create SQL queries that will be
    executed to get the the desired information for the specified time range.

    ## Schema
    Columns:
    - timestamp_string: string (ISO8601 formatted timestamp)
    - description: string (AI-generated description of the camera view)
    - stream_name: string (Identifier for the camera location)
    - ingest_date: string (Partition key, format: YYYY-MM-DD)

    Partitioned by: ingest_date
    Sorted by: timestamp_string (descending)

    Sample row:
    "timestamp_string": "2025-01-10T20:51:28+00:00",
    "description": "The kitchen is empty with a dining table and chairs visible.",
    "stream_name": "kitchen",
    "ingest_date": "2025-01-10"

    ## Example queries
    {sample_queries}

    Given the above schema, create a SQL query that will return the data for:
    stream_name = '{camera_location}'
    and
    between {timestamp_start} and {timestamp_end}.

    Respond with the query witin markdown tags:
    ```sql
    <query>
    ```
    """

    message_list = [
        {
            "role": "user",
            "content": [
                {"text": get_sql_prompt},
            ],
        }
    ]

    inf_params = {
        "max_new_tokens": 1000,
        "top_p": 0.1,
        "top_k": 20,
        "temperature": 0,
    }

    try:
        return invoke_bedrock_model(MODEL_ID, message_list, inf_params=inf_params)
    except Exception as e:
        if "ThrottlingException" in str(e):
            return "The request to generate sql to query the camera history was throttled... You should wait a bit"
        raise


def get_sample_queries(camera_location: str, table_name: str) -> str:
    """Return a string of sample queries for the given camera location."""
    return f"""
    SELECT *
    FROM "{table_name}"
    WHERE ingest_date IN (
        date_format(current_date, '%Y-%m-%d'),
        date_format(current_date - interval '1' day, '%Y-%m-%d')
    )
    AND from_iso8601_timestamp(timestamp_string) >= current_timestamp - interval '5' minute
    AND stream_name = '{camera_location}'
    ORDER BY from_iso8601_timestamp(timestamp_string) DESC


    SELECT *
    FROM "{table_name}"
    WHERE ingest_date IN (
        '2023-05-01',
        '2023-05-02'
    )
    AND from_iso8601_timestamp(timestamp_string) >= from_iso8601_timestamp('2023-05-01T00:00:00Z')
    AND from_iso8601_timestamp(timestamp_string) < from_iso8601_timestamp('2023-05-02T00:00:00Z')
    AND stream_name = '{camera_location}'
    ORDER BY from_iso8601_timestamp(timestamp_string) DESC

    
    SELECT *
    FROM "{table_name}"
    WHERE ingest_date IN (
        date_format(current_date, '%Y-%m-%d'),
        date_format(current_date - interval '1' day, '%Y-%m-%d')
    )
    AND from_iso8601_timestamp(timestamp_string) >= current_timestamp - interval '10' minute
    AND from_iso8601_timestamp(timestamp_string) <= current_timestamp
    AND stream_name = '{camera_location}'
    ORDER BY from_iso8601_timestamp(timestamp_string) DESC

    
    SELECT *
    FROM "{table_name}"
    WHERE ingest_date >= date_format(current_date - interval '7' day, '%Y-%m-%d')
    AND ingest_date <= date_format(current_date, '%Y-%m-%d')
    AND from_iso8601_timestamp(timestamp_string) >= date_trunc('day', current_timestamp - interval '7' day)
    AND from_iso8601_timestamp(timestamp_string) <= current_timestamp
    AND stream_name = '{camera_location}'
    ORDER BY from_iso8601_timestamp(timestamp_string) DESC
    """
