"""
Lambda function that bridges Bedrock Agent action group calls to Apache Tika
running on ECS Fargate behind an internal ALB.
"""

import json
import logging
import os
import base64
import time
import urllib.request
import urllib.error
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TIKA_URL = os.environ["TIKA_URL"]
DOCS_BUCKET = os.environ.get("DOCS_BUCKET", "")
s3_client = boto3.client("s3")

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1  # seconds
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB — safe limit for 256 MB Lambda


def handler(event, context):
    """Handle Bedrock Agent action group invocations."""
    api_path = event.get("apiPath", "")
    http_method = event.get("httpMethod", "GET")
    request_body = event.get("requestBody", {})

    logger.info("Received request: api_path=%s method=%s", api_path, http_method)

    if api_path == "/process-s3-file" and http_method == "POST":
        return process_s3_file(event, request_body)
    elif api_path == "/extract-text" and http_method == "POST":
        return extract_text(event, request_body)
    elif api_path == "/detect-type" and http_method == "POST":
        return detect_type(event, request_body)
    elif api_path == "/extract-metadata" and http_method == "POST":
        return extract_metadata(event, request_body)
    else:
        return build_response(event, 400, {"error": f"Unknown path: {api_path}"})


def _call_tika(tika_path, file_bytes, content_type, accept, timeout=90):
    """Call a Tika endpoint with retry logic for transient failures."""
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                f"{TIKA_URL}{tika_path}",
                data=file_bytes,
                headers={"Content-Type": content_type, "Accept": accept},
                method="PUT",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.URLError, ConnectionError) as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                sleep_time = RETRY_BACKOFF_BASE * (2**attempt)
                logger.warning(
                    "Tika call failed (attempt %d/%d): %s. Retrying in %ds",
                    attempt + 1,
                    MAX_RETRIES,
                    e,
                    sleep_time,
                )
                time.sleep(sleep_time)
    raise last_error


def _decode_base64(value):
    """Decode a base64 string, returning bytes or None on failure."""
    try:
        return base64.b64decode(value)
    except Exception:
        return None


def _check_payload_size(event, file_bytes):
    """Return an error response if decoded payload exceeds the size limit, else None."""
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        logger.warning("Payload too large: %d bytes", len(file_bytes))
        return build_response(
            event,
            400,
            {
                "error": f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB"
            },
        )
    return None


def _get_content_from_body(request_body):
    """Extract content properties from the Bedrock Agent request body."""
    if not request_body:
        return None
    content = request_body.get("content", {})
    app_json = content.get("application/json", {})
    if app_json and "properties" in app_json:
        props = {}
        for prop in app_json["properties"]:
            props[prop["name"]] = prop["value"]
        return props
    return None


def extract_text(event, request_body):
    """Extract text from a document via Tika /tika endpoint."""
    content = _get_content_from_body(request_body)
    if not content or "document_base64" not in content:
        return build_response(event, 400, {"error": "document_base64 is required"})

    file_bytes = _decode_base64(content["document_base64"])
    if file_bytes is None:
        return build_response(event, 400, {"error": "Invalid base64 encoding"})

    size_error = _check_payload_size(event, file_bytes)
    if size_error:
        return size_error

    content_type = content.get("content_type", "application/octet-stream")
    try:
        text = _call_tika("/tika", file_bytes, content_type, "text/plain")
        return build_response(event, 200, {"extracted_text": text})
    except Exception as e:
        logger.error("extract_text failed: %s", e)
        return build_response(event, 500, {"error": "Text extraction failed"})


def detect_type(event, request_body):
    """Detect MIME type of a document via Tika /detect endpoint."""
    content = _get_content_from_body(request_body)
    if not content or "document_base64" not in content:
        return build_response(event, 400, {"error": "document_base64 is required"})

    file_bytes = _decode_base64(content["document_base64"])
    if file_bytes is None:
        return build_response(event, 400, {"error": "Invalid base64 encoding"})

    size_error = _check_payload_size(event, file_bytes)
    if size_error:
        return size_error

    try:
        mime_type = _call_tika(
            "/detect/stream",
            file_bytes,
            "application/octet-stream",
            "text/plain",
            timeout=30,
        )
        return build_response(event, 200, {"mime_type": mime_type.strip()})
    except Exception as e:
        logger.error("detect_type failed: %s", e)
        return build_response(event, 500, {"error": "MIME type detection failed"})


def extract_metadata(event, request_body):
    """Extract metadata from a document via Tika /meta endpoint."""
    content = _get_content_from_body(request_body)
    if not content or "document_base64" not in content:
        return build_response(event, 400, {"error": "document_base64 is required"})

    file_bytes = _decode_base64(content["document_base64"])
    if file_bytes is None:
        return build_response(event, 400, {"error": "Invalid base64 encoding"})

    size_error = _check_payload_size(event, file_bytes)
    if size_error:
        return size_error

    content_type = content.get("content_type", "application/octet-stream")
    try:
        result = _call_tika(
            "/meta", file_bytes, content_type, "application/json", timeout=30
        )
        return build_response(event, 200, {"metadata": json.loads(result)})
    except Exception as e:
        logger.error("extract_metadata failed: %s", e)
        return build_response(event, 500, {"error": "Metadata extraction failed"})


def process_s3_file(event, request_body):
    """Fetch a file from S3 and process it via Tika."""
    content = _get_content_from_body(request_body)
    if not content or "s3_key" not in content:
        return build_response(event, 400, {"error": "s3_key is required"})

    s3_key = content["s3_key"]
    action = content.get("action", "extract_text")
    valid_actions = ("extract_text", "extract_metadata", "detect_type")
    if action not in valid_actions:
        return build_response(
            event,
            400,
            {
                "error": f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}"
            },
        )

    logger.info(
        "Processing S3 file: bucket=%s key=%s action=%s", DOCS_BUCKET, s3_key, action
    )

    try:
        head = s3_client.head_object(Bucket=DOCS_BUCKET, Key=s3_key)
        file_size = head.get("ContentLength", 0)
        if file_size > MAX_FILE_SIZE_BYTES:
            logger.warning(
                "File too large: s3://%s/%s (%d bytes)", DOCS_BUCKET, s3_key, file_size
            )
            return build_response(
                event,
                400,
                {
                    "error": f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB"
                },
            )
        s3_obj = s3_client.get_object(Bucket=DOCS_BUCKET, Key=s3_key)
        file_bytes = s3_obj["Body"].read()
        content_type = s3_obj.get("ContentType", "application/octet-stream")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error("S3 error (%s): %s", error_code, e)
        if error_code in ("NoSuchKey", "NoSuchBucket"):
            return build_response(
                event, 400, {"error": f"Not found: s3://{DOCS_BUCKET}/{s3_key}"}
            )
        return build_response(event, 500, {"error": "Failed to retrieve file from S3"})
    except Exception as e:
        logger.error("Unexpected S3 error: %s", e)
        return build_response(event, 500, {"error": "Failed to retrieve file from S3"})

    if action == "detect_type":
        tika_path, accept = "/detect/stream", "text/plain"
    elif action == "extract_metadata":
        tika_path, accept = "/meta", "application/json"
    else:
        tika_path, accept = "/tika", "text/plain"

    try:
        result = _call_tika(tika_path, file_bytes, content_type, accept)
        if action == "extract_metadata":
            return build_response(
                event, 200, {"s3_key": s3_key, "metadata": json.loads(result)}
            )
        elif action == "detect_type":
            return build_response(
                event, 200, {"s3_key": s3_key, "mime_type": result.strip()}
            )
        else:
            return build_response(
                event, 200, {"s3_key": s3_key, "extracted_text": result}
            )
    except Exception as e:
        logger.error(
            "Tika processing failed for s3://%s/%s: %s", DOCS_BUCKET, s3_key, e
        )
        return build_response(event, 500, {"error": "File processing failed"})


def build_response(event, status_code, body):
    """Build a Bedrock Agent action group response."""
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", "TikaDocumentProcessor"),
            "apiPath": event.get("apiPath", "/"),
            "httpMethod": event.get("httpMethod", "GET"),
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(body),
                }
            },
        },
    }
