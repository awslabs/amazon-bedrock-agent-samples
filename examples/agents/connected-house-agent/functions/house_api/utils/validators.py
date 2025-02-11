from typing import Tuple, List
from datetime import datetime


def validate_camera_request(
    camera: str, question: str, valid_cameras: List[str]
) -> Tuple[bool, str]:
    """Validate camera request parameters."""
    if not camera:
        return False, "Missing required camera parameter"
    if camera not in valid_cameras:
        return (
            False,
            f"Invalid camera location. Available cameras: {', '.join(valid_cameras)}",
        )
    if not question:
        return False, "Missing required question parameter"
    return True, ""


def validate_camera_history_request(
    camera: str,
    question: str,
    start_timestamp: str,
    end_timestamp: str,
    valid_cameras: List[str],
) -> Tuple[bool, str]:
    """Validate camera history request parameters."""

    is_valid, error_message = validate_camera_request(camera, question, valid_cameras)
    if not is_valid:
        return False, error_message

    if not start_timestamp:
        return False, "Missing required start_timestamp property"
    if not end_timestamp:
        return False, "Missing required end_timestamp property"

    return True, ""


# validators.py
from datetime import datetime
from typing import Tuple, List, Optional


def validate_clip_request(
    camera: str, start_timestamp: str, end_timestamp: str, valid_cameras: List[str]
) -> Tuple[bool, str, Optional[tuple[datetime, datetime]]]:
    """Validate clip creation request parameters."""
    # Validate camera
    if not camera:
        return False, "Bad request - Missing required camera parameter", None

    if camera not in valid_cameras:
        return (
            False,
            f"Invalid camera location. Available cameras: {', '.join(valid_cameras)}",
            None,
        )

    # Validate timestamps presence
    if not start_timestamp or not end_timestamp:
        return False, "Bad request - Missing required timestamp parameters", None

    # Validate timestamp format and convert to datetime
    try:
        start_time = datetime.fromisoformat(start_timestamp.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(end_timestamp.replace("Z", "+00:00"))

        return True, "", (start_time, end_time)

    except ValueError as e:
        return False, f"Invalid timestamp format: {str(e)}", None
