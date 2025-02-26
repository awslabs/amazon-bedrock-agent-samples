import boto3
import json
import os

STATEMACHINE_ARN = os.getenv("STATEMACHINE_ARN")


def lambda_handler(event, context):
    step_functions = boto3.client("stepfunctions")

    camera_streams = ["diningroom", "backyard", "kitchen", "livingroom"]

    for stream in camera_streams:
        step_functions.start_execution(
            stateMachineArn=STATEMACHINE_ARN, input=json.dumps({"streamName": stream})
        )
