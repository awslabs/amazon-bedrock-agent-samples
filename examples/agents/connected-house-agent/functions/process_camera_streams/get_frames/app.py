import boto3
import base64
import os

from io import BytesIO
from datetime import datetime, timedelta
from aws_lambda_powertools import Logger


# Environment variables
FRAMES_BUCKET = os.environ["FRAMES_BUCKET"]
SAMPLING_INTERVAL_MS = 3000  # 3 seconds
FRAMES_PER_GROUP = 25

# Initialize AWS clients
s3_client = boto3.client("s3")
kvs_client = boto3.client("kinesisvideo")

logger = Logger()


def lambda_handler(event, context):
    try:
        stream_name = event["Payload"]["streamName"]

        client = get_kvs_client(stream_name)

        start_time, end_time = get_time_range()

        frames = get_frames(client, stream_name, start_time, end_time)

        if not frames:
            logger.info("No images returned in the specified time range.")
            return []

        frame_groups = process_frames(frames, stream_name)

        return frame_groups

    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        raise


def get_kvs_client(stream_name):
    """Get KVS client with the appropriate endpoint."""
    endpoint = kvs_client.get_data_endpoint(
        StreamName=stream_name,
        APIName="GET_IMAGES",
    )["DataEndpoint"]
    return boto3.client("kinesis-video-archived-media", endpoint_url=endpoint)


def get_time_range():
    """Get the start and end time for the last minute."""
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=1)
    return start_time, end_time


def get_frames(client, stream_name, start_time, end_time):
    """Retrieve frames from KVS."""
    response = client.get_images(
        StreamName=stream_name,
        ImageSelectorType="SERVER_TIMESTAMP",
        StartTimestamp=start_time,
        EndTimestamp=end_time,
        SamplingInterval=SAMPLING_INTERVAL_MS,
        Format="PNG",
    )

    if "Errors" in response and any(
        err.get("Code") == "NO_MEDIA" for err in response["Errors"]
    ):
        logger.info("NO_MEDIA: No media available for the specified time range.")
        return []

    return response.get("Images", [])


def process_frames(frames, stream_name):
    """Process and group frames."""
    logger.info(f"Retrieved {len(frames)} images")

    frame_groups = []
    current_group = []

    for frame in frames:
        if "Error" in frame:
            continue

        frame_data = process_single_frame(frame, stream_name)
        current_group.append(frame_data)

        if len(current_group) == FRAMES_PER_GROUP:
            frame_groups.append(current_group)
            current_group = []

    # Add any remaining frames as a group
    if current_group:
        frame_groups.append(current_group)

    return frame_groups


def process_single_frame(frame, stream_name):
    """Process a single frame: decode, upload to S3, and return metadata."""
    image_data = base64.b64decode(frame["ImageContent"])
    image_file = BytesIO(image_data)

    timestamp = frame["TimeStamp"]
    s3_frame_key = f"frames/{timestamp.isoformat()}_{os.urandom(4).hex()}.png"

    try:
        s3_client.upload_fileobj(image_file, FRAMES_BUCKET, s3_frame_key)
    except Exception as e:
        logger.error(f"Error uploading frame to S3: {str(e)}")
        raise

    return {
        "timestamp_string": timestamp.isoformat(),
        "s3_frame_key": s3_frame_key,
        "stream_name": stream_name,
    }
