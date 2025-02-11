import time
import os
import re
import boto3
import requests
from typing import Dict, Any, Union

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

from utils.bedrock_utils import (
    analyze_camera_image,
    analyze_camera_history,
    generate_sql_query,
)
from utils.kvs_utils import generate_and_upload_clip, get_latest_frame_from_camera
from utils.athena_utils import execute_athena_query
from utils.validators import (
    validate_camera_request,
    validate_camera_history_request,
    validate_clip_request,
)

# Environment variables
API_KEY = os.environ["OPENWEATHER_API_KEY"]
WEATHER_LOCATION = os.environ["WEATHER_LOCATION"]
CLIP_BUCKET = os.environ["CLIP_BUCKET"]
ATHENA_BUCKET = os.environ["ATHENA_BUCKET"]
ATHENA_DATABASE = os.environ["ATHENA_DATABASE"]
CAMERA_TABLE_NAME = os.environ["CAMERA_TABLE_NAME"]
TEMP_DDB_TABLE = os.environ["TEMP_DDB_TABLE"]

# Weather API Constants
BASE_WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"

# Athena constants
ATHENA_GENERATE_SQL_MAX_TRIES = 3

# Initialize AWS clients
athena_client = boto3.client("athena")
bedrock_client = boto3.client("bedrock-runtime")
kvs_client = boto3.client("kinesisvideo")
dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table(TEMP_DDB_TABLE)  # Replace with your table name

# Define cameras
CAMERA_STREAMS = ["backyard", "kitchen", "livingroom", "diningroom"]
TEMPERATURE_SENSORS = ["guestroom", "pannrum"]

logger = Logger()

app = APIGatewayRestResolver()


@app.get("/temp", description="Get the current reading from indoor thermometers")
def get_temp() -> Dict[str, Any]:
    """Return the current temperature and humidity readings from sensors throughout the house."""
    try:
        return get_latest_temperature()
    except Exception as e:
        logger.error(f"Error fetching temperature data: {str(e)}")
        return {"error": "Failed to retrieve temperature data"}, 500


@app.get("/weather", description="Get the current outside weather information")
def get_weather() -> Dict[str, Any]:
    """Return the current outside weather for the provided location."""
    try:
        weather_info = fetch_weather("Hassela")
        if weather_info is None:
            return {
                "error": "Could not retrieve weather data for the specified location."
            }, 400
        return weather_info

    except Exception as e:
        logger.error(f"Error fetching weather data: {str(e)}")
        return {"error": "Failed to retrieve weather data"}, 500


@app.post(
    "/camera",
    description="Endpoint to ask a question about what a specific camera observes",
)
def ask_camera() -> Dict[str, Any]:
    """Process questions about camera images."""
    body = app.current_event.json_body or {}
    camera_location = body.get("camera")
    question = body.get("question")

    # Validate input
    is_valid, error_message = validate_camera_request(
        camera_location, question, CAMERA_STREAMS
    )
    if not is_valid:
        return {"error": error_message}, 400

    try:
        logger.info(f"Asking {camera_location} camera question: {question}")
        response = get_latest_frame_from_camera(camera_location)

        if "Images" not in response or not response["Images"]:
            return {
                "error": f"No video data currently available in stream for {camera_location} camera"
            }, 200

        base64_encoded_image = response["Images"][0]["ImageContent"]

        response = analyze_camera_image(base64_encoded_image, camera_location, question)

        return {"message": response}, 200

    except Exception as e:
        logger.error(f"Error processing camera request for {camera_location}: {str(e)}")
        return {"error": f"Internal server error: {str(e)}"}, 500


@app.post(
    "/camera/history", description="Endpoint to ask a question about camera history"
)
def ask_camera_history() -> Dict[str, Any]:
    body = app.current_event.json_body or {}
    camera_location = body.get("camera")
    question = body.get("question")
    start_timestamp = body.get("start_timestamp")
    end_timestamp = body.get("end_timestamp")

    # Validate input
    is_valid, error_message = validate_camera_history_request(
        camera_location, question, start_timestamp, end_timestamp, CAMERA_STREAMS
    )

    if not is_valid:
        return {"error": error_message}, 400

    retry_count = 0
    query = None

    while retry_count < ATHENA_GENERATE_SQL_MAX_TRIES and not query:
        query_generation_response = generate_sql_query(
            camera_location, start_timestamp, end_timestamp, CAMERA_TABLE_NAME
        )
        logger.info(query_generation_response)
        query = extract_last_sql_query(query_generation_response)
        if not query:
            retry_count += 1
            time.sleep(1)

    if not query:
        return {
            "message": "Error in generating SQL - Could not generate valid SQL query after 3 attempts"
        }, 200

    history = execute_athena_query(query, ATHENA_DATABASE, ATHENA_BUCKET)

    logger.info(
        f"For camera location {camera_location} the history length is: {len(history)}"
    )

    response = analyze_camera_history(history, question)

    logger.info(response)

    return {"message": response}, 200


@app.post(
    "/camera/clip",
    description="Generate a video clip from a camera stream between two timestamps",
)
def create_clip() -> Dict[str, Any]:
    body = app.current_event.json_body or {}
    camera_location = body.get("camera")
    start_timestamp = body.get("start_timestamp")
    end_timestamp = body.get("end_timestamp")

    # Validate input
    is_valid, error_message, timestamps = validate_clip_request(
        camera_location, start_timestamp, end_timestamp, CAMERA_STREAMS
    )

    if not is_valid:
        return {"error": error_message}, 400

    try:
        # Convert string timestamps to datetime objects
        start_time, end_time = timestamps

        # Get video clip and upload to S3
        video_url = generate_and_upload_clip(
            camera_location, start_time, end_time, CLIP_BUCKET
        )

        return {"url": video_url}, 200

    except ValueError as e:
        return {"error": f"Invalid timestamp format: {str(e)}"}, 400
    except Exception as e:
        logger.error(f"Error generating video clip: {str(e)}")
        return {"error": f"Internal server error: {str(e)}"}, 500


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> Dict[str, Any]:
    """Main Lambda handler to resolve incoming requests to the correct route."""
    return app.resolve(event, context)


def extract_last_sql_query(text):
    # Pattern to match ```sql <query> ``` blocks
    pattern = r"```sql\s*(.*?)\s*```"

    # Find all matches in the text
    matches = re.findall(pattern, text, re.DOTALL)

    # If matches found, return the last one, otherwise return None
    if matches:
        return matches[-1].strip()
    else:
        return None


def fetch_weather(location: str) -> Union[Dict[str, Any], None]:
    """Fetch weather data for a specified location from the OpenWeather API."""
    if API_KEY == "test":
        return {
            "location": location,
            "temperature": -9,
            "weather_description": "Clear skies",
        }

    params = {
        "q": location,
        "appid": API_KEY,
        "units": "metric",
    }
    try:
        response = requests.get(BASE_WEATHER_URL, params=params)
        response.raise_for_status()
        weather_data = response.json()
        return {
            "location": location,
            "temperature": weather_data["main"]["temp"],
            "weather_description": weather_data["weather"][0]["description"],
        }
    except requests.RequestException as e:
        logger.error(f"Error fetching weather data: {e}")
        return None


def get_latest_temperature() -> Dict[str, Any]:
    """
    Fetches the latest temperature readings from DynamoDB for guestroom and pannrum.
    Returns data formatted according to the OpenAPI specification, with messages for missing readings.
    """

    def get_latest_reading(location: str) -> Dict[str, Any]:
        """Helper function to get latest reading for a specific location"""
        response = table.query(
            KeyConditionExpression="pk = :pk",
            ExpressionAttributeValues={":pk": location},
            ScanIndexForward=False,  # Sort in descending order (newest first)
            Limit=1,
        )

        if not response["Items"]:
            return {"error": f"No readings available for {location}"}

        item = response["Items"][0]
        return {
            "temp": [float(item.get("temp"))],
            "humidity": [float(item.get("humidity"))],
            "timestamp": item["sk"],
        }

    # Get readings for all sensors
    response = {}

    for sensor in TEMPERATURE_SENSORS:
        sensor_data = get_latest_reading(sensor)
        if "error" in sensor_data:
            response[sensor] = {"message": sensor_data["error"]}
        else:
            response[sensor] = sensor_data

    return response
