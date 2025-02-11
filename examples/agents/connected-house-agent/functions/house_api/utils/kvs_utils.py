import boto3
import os

from datetime import datetime, timedelta, timezone


def generate_and_upload_clip(
    stream_name: str,
    start_time: datetime,
    end_time: datetime,
    bucket_name: str,
) -> str:
    """
    Generate a video clip and upload it to S3.
    Returns a presigned URL for the uploaded video.
    """
    s3_client = boto3.client("s3")

    # Generate unique filename
    filename = f"{stream_name}_{start_time.strftime('%Y%m%d_%H%M%S')}.mp4"

    response = get_clip(stream_name, start_time, end_time)

    # Upload to S3
    s3_key = f"clips/{filename}"
    s3_client.upload_fileobj(
        response["Payload"],
        bucket_name,
        s3_key,
        ExtraArgs={"ContentType": "video/mp4"},
    )

    # Generate presigned URL (valid for 1 hour)
    presigned_url = s3_client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket_name, "Key": s3_key}, ExpiresIn=3600
    )

    return presigned_url


def get_clip(stream_name, start_time, end_time):
    kvs_client = boto3.client("kinesisvideo")

    # Get KVS endpoint for clip generation
    endpoint = kvs_client.get_data_endpoint(StreamName=stream_name, APIName="GET_CLIP")[
        "DataEndpoint"
    ]

    # Create KVS archived media client
    archived_media_client = boto3.client(
        "kinesis-video-archived-media",
        endpoint_url=endpoint,
        region_name=os.environ["AWS_REGION"],
    )
    # Get the clip
    response = archived_media_client.get_clip(
        StreamName=stream_name,
        ClipFragmentSelector={
            "FragmentSelectorType": "SERVER_TIMESTAMP",
            "TimestampRange": {
                "StartTimestamp": start_time,
                "EndTimestamp": end_time,
            },
        },
    )

    return response


def get_latest_frame_from_camera(stream_name: str):
    kvs_client = boto3.client("kinesisvideo")

    # Get kvs data endpoint
    endpoint = kvs_client.get_data_endpoint(
        StreamName=stream_name,
        APIName="GET_IMAGES",
    )["DataEndpoint"]

    # Create kvs archive client with above data endpoint
    archived_media_client = boto3.client(
        "kinesis-video-archived-media",
        endpoint_url=endpoint,
        region_name=os.environ["AWS_REGION"],
    )

    # Fetch an image from the camera
    end_timestamp = datetime.now(timezone.utc)
    start_timestamp = end_timestamp - timedelta(seconds=5)

    response = archived_media_client.get_images(
        StreamName=stream_name,
        ImageSelectorType="PRODUCER_TIMESTAMP",
        StartTimestamp=start_timestamp,
        EndTimestamp=end_timestamp,
        MaxResults=1,
        Format="JPEG",
    )

    return response
