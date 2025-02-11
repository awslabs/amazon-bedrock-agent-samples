import json
import os
import boto3
import base64
from aws_lambda_powertools import Logger

# Environment variables
FRAMES_BUCKET = os.environ["FRAMES_BUCKET"]
DELIVERY_STREAM = os.environ["DELIVERY_STREAM"]
MODEL_ID = os.environ["MODEL_ID"]


# Initialize AWS clients
s3_client = boto3.client("s3")
firehose_client = boto3.client("firehose")
bedrock_client = boto3.client("bedrock-runtime", region_name="us-west-2")


# Set up logging
logger = Logger()


def lambda_handler(event, context):
    try:
        payload = event["Payload"]
        timestamp_string = payload[0]["timestamp_string"]
        stream_name = payload[0]["stream_name"]

        encoded_images = [encode_image(image["s3_frame_key"]) for image in payload]

        prompt = get_prompt(stream_name)
        model_payload = get_prompt_payload(encoded_images, prompt)

        response = invoke_model(model_payload)
        description = get_completion_from_response(response)

        logger.info(f"Report for {stream_name}: {description}")

        result_payload = {
            "timestamp_string": timestamp_string,
            "description": description,
            "stream_name": stream_name,
        }

        push_to_firehose(result_payload)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Processing completed successfully"}),
        }

    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def encode_image(s3_frame_key):
    try:
        response = s3_client.get_object(Bucket=FRAMES_BUCKET, Key=s3_frame_key)
        image_bytes = response["Body"].read()
        return base64.b64encode(image_bytes).decode("utf-8")
    except Exception as e:
        logger.error(f"Error encoding image {s3_frame_key}: {str(e)}")
        raise


def get_prompt(stream_name):
    return f"""
    ## Instructions
    Analyze the provided images above from a surveillance camera in the {stream_name}. 
    Focus on people, animals, general movement, and anything noteworthy for a homeowner's analysis and alerting.
    The images are taken from the same camera a few seconds apart. 
    Provide a concise description in flowing text, focusing on things a homeowner may be interested in 
    when asking questions about their home cameras, specifically about movement and other noteworthy things.
    A hint that something is happening is if the images provided above are different in any way, but it's necessarily so.

    ## Rules
    - Do NOT mention anything about if the images are different or not - I'm only interested in what's going on in the images, if there's something going on.
    - Do NOT simply describe the room and it's contents. If there's no activity, simply say "No activity detected".
    - Do NOT include information from the timestamp in the report.
    - Only include information you are certain of are in the images.
    - Create a description in flowing text, make sure you capture everything of interest. No bullet points.
    """


def get_prompt_payload(encoded_images, prompt):
    content = []

    for encoded_image in encoded_images:
        content.append(
            {
                "image": {
                    "format": "png",
                    "source": {"bytes": encoded_image},
                }
            }
        )

    content.append({"text": prompt})

    prompt_config = {
        "inferenceConfig": {
            "max_new_tokens": 300,
            "temperature": 0,
        },
        "messages": [
            {
                "role": "user",
                "content": content,
            }
        ],
    }

    return json.dumps(prompt_config)


def invoke_model(payload):
    try:
        response = bedrock_client.invoke_model(
            body=payload,
            modelId=MODEL_ID,
        )
        return json.loads(response.get("body").read())
    except Exception as e:
        logger.error(f"Error invoking model: {str(e)}")
        raise


def get_completion_from_response(response):
    return response["output"]["message"]["content"][0]["text"]


def push_to_firehose(json_payload):
    try:
        firehose_client.put_record(
            DeliveryStreamName=DELIVERY_STREAM,
            Record={"Data": json.dumps(json_payload) + "\n"},
        )
    except Exception as e:
        logger.error(f"Error pushing to Firehose: {str(e)}")
        raise
