import json
import os
import requests
import boto3

from typing import Dict, Any
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from urllib.parse import urlparse
from aws_lambda_powertools import Logger

# Set up logging
logger = Logger()

# Get environment variables
BASE_URL = os.environ["BASE_URL"]


def gen_iam_signature(base_url):
    # Gather the domain name and AWS region
    url = urlparse(base_url)
    region = boto3.session.Session().region_name

    # Create the signature helper
    iam_auth = BotoAWSRequestsAuth(
        aws_host=url.netloc, aws_region=region, aws_service="execute-api"
    )

    return iam_auth


def make_api_request(
    endpoint: str, method: str = "GET", data: Dict = None
) -> Dict[str, Any]:
    """
    Makes a request to the specified API endpoint

    Args:
        endpoint (str): The API endpoint to call
        method (str): HTTP method to use (GET or POST)
        data (Dict): Data to send in the request body for POST requests

    Returns:
        Dict[str, Any]: The JSON response from the API
    """

    if data:
        logger.info(
            f"Post request sent to Hassela API. Endpoint: {endpoint}, Data: {data}"
        )

    iam_auth = gen_iam_signature(BASE_URL)

    try:
        if method.upper() == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", auth=iam_auth)
        else:  # POST
            response = requests.post(f"{BASE_URL}{endpoint}", auth=iam_auth, json=data)

        response.raise_for_status()
        logger.info(response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")


def get_weather() -> Dict[str, Any]:
    """
    Fetches weather information from the /weather endpoint

    Returns:
        Dict[str, Any]: Weather information including location, temperature, and description
    """
    logger.info("Fetching weather data")
    return make_api_request("weather")


def get_temperature() -> Dict[str, Any]:
    """
    Fetches temperature information from the /temp endpoint

    Returns:
        Dict[str, Any]: Temperature and humidity data for different rooms
    """
    logger.info("Fetching temperature data")
    return make_api_request("temp")


def ask_camera(camera: str, question: str) -> Dict[str, Any]:
    """
    Sends a question to the unified camera endpoint

    Args:
        camera (str): The camera location (backyard, kitchen, livingroom, diningroom)
        question (str): The question to ask about the camera observations

    Returns:
        Dict[str, Any]: Response containing the answer to the camera question
    """
    logger.info(f"Asking {camera} camera question: {question}")
    return make_api_request(
        "camera", method="POST", data={"camera": camera, "question": question}
    )


def ask_camera_history(
    camera: str, question: str, start_timestamp: str, end_timestamp: str
) -> Dict[str, Any]:
    """
    Sends a historical question to the unified camera history endpoint

    Args:
        camera (str): The camera location (backyard, kitchen, livingroom, diningroom)
        question (str): The question to ask about the camera observations
        start_timestamp (str): Start time of the period to query (ISO8601 format)
        end_timestamp (str): End time of the period to query (ISO8601 format or "now")

    Returns:
        Dict[str, Any]: Response containing the answer to the historical camera question
    """
    logger.info(f"Asking {camera} camera historical question: {question}")
    return make_api_request(
        "camera/history",
        method="POST",
        data={
            "camera": camera,
            "question": question,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        },
    )


def get_camera_clip(
    camera: str, start_timestamp: str = None, end_timestamp: str = None
) -> Dict[str, Any]:
    """
    Requests a video clip from the unified clip endpoint

    Args:
        camera (str): The camera location (backyard, kitchen, livingroom, diningroom)
        start_timestamp (str, optional): Start time of the clip (ISO8601 format)
        end_timestamp (str, optional): End time of the clip (ISO8601 format)

    Returns:
        Dict[str, Any]: Response containing the URL to download the generated video clip
    """
    logger.info(f"Requesting clip from {camera} camera")
    data = {"camera": camera}
    if start_timestamp:
        data["start_timestamp"] = start_timestamp
    if end_timestamp:
        data["end_timestamp"] = end_timestamp

    return make_api_request("camera/clip", method="POST", data=data)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler function that processes incoming requests from Bedrock agent

    Args:
        event (Dict[str, Any]): The event data from the Bedrock agent
        context (Any): Lambda context

    Returns:
        Dict[str, Any]: Response containing the requested information
    """
    logger.info("Lambda function invoked")
    logger.info(event)

    try:
        api_path = event.get("apiPath", "")

        if api_path == "/getWeather":
            response_data = get_weather()

        elif api_path == "/getTemperature":
            response_data = get_temperature()

        elif api_path == "/askCamera":
            # Extract data from the request body
            request_body = event.get("requestBody", "{}")
            request_body = request_body["content"]["application/json"]["properties"]

            # Initialize variables
            camera = None
            question = None

            # Extract values from properties
            for prop in request_body:
                if prop["name"] == "camera":
                    camera = prop["value"].lower()
                elif prop["name"] == "question":
                    question = prop["value"]

            # Validate inputs
            if not camera or not question:
                raise ValueError("Both camera and question are required")

            # Validate camera location
            valid_locations = ["backyard", "kitchen", "livingroom", "diningroom"]
            if camera not in valid_locations:
                raise ValueError(
                    f"Invalid camera location. Must be one of: {', '.join(valid_locations)}"
                )

            response_data = ask_camera(camera, question)

        elif api_path == "/askCamera/history":
            # Extract data from the request body
            request_body = event.get("requestBody", "{}")
            request_body = request_body["content"]["application/json"]["properties"]

            # Initialize variables
            camera = None
            question = None
            start_timestamp = None
            end_timestamp = None

            # Extract values from properties
            for prop in request_body:
                if prop["name"] == "camera":
                    camera = prop["value"].lower()
                elif prop["name"] == "question":
                    question = prop["value"]
                elif prop["name"] == "start_timestamp":
                    start_timestamp = prop["value"]
                elif prop["name"] == "end_timestamp":
                    end_timestamp = prop["value"]

            # Validate inputs
            if not all([camera, question, start_timestamp]):
                raise ValueError("Camera, question, and start_timestamp are required")

            # Validate camera location
            valid_locations = ["backyard", "kitchen", "livingroom", "diningroom"]
            if camera not in valid_locations:
                raise ValueError(
                    f"Invalid camera location. Must be one of: {', '.join(valid_locations)}"
                )

            response_data = ask_camera_history(
                camera, question, start_timestamp, end_timestamp
            )

        elif api_path == "/getClip":
            # Extract data from the request body
            request_body = event.get("requestBody", "{}")
            request_body = request_body["content"]["application/json"]["properties"]

            # Initialize variables
            camera = None
            start_timestamp = None
            end_timestamp = None

            # Extract values from properties
            for prop in request_body:
                if prop["name"] == "camera":
                    camera = prop["value"].lower()
                elif prop["name"] == "start_timestamp":
                    start_timestamp = prop["value"]
                elif prop["name"] == "end_timestamp":
                    end_timestamp = prop["value"]

            # Validate inputs
            if not camera or not start_timestamp:
                raise ValueError("Camera and start_timestamp are required")

            # Validate camera location
            valid_locations = ["backyard", "kitchen", "livingroom", "diningroom"]
            if camera not in valid_locations:
                raise ValueError(
                    f"Invalid camera location. Must be one of: {', '.join(valid_locations)}"
                )

            response_data = get_camera_clip(camera, start_timestamp, end_timestamp)

        else:
            response_data = {f"{api_path} is not a valid api, try another one."}

        response_body = {"application/json": {"body": json.dumps(response_data)}}

        action_response = {
            "actionGroup": event["actionGroup"],
            "apiPath": event["apiPath"],
            "httpMethod": event["httpMethod"],
            "httpStatusCode": 200,
            "responseBody": response_body,
        }

        logger.info(action_response)
        return {"messageVersion": "1.0", "response": action_response}

    except Exception as e:
        action_response = {
            "actionGroup": event["actionGroup"],
            "apiPath": event["apiPath"],
            "httpMethod": event["httpMethod"],
            "httpStatusCode": 200,
            "responseBody": {"error": str(e)},
        }

        logger.error(f"Error: {str(e)}")
        return {"messageVersion": "1.0", "response": action_response}
