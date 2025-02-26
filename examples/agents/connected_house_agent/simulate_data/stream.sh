#!/bin/bash

# Check for required AWS environment variables
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$AWS_DEFAULT_REGION" ]; then
    echo "Error: AWS credentials not set. Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION"
    exit 1
fi

if [ -z "$STREAM_NAME" ]; then
    echo "Error: STREAM_NAME environment variable not set"
    exit 1
fi

if [ -z "$VIDEO_FILE" ]; then
    echo "Error: VIDEO_FILE environment variable not set"
    exit 1
fi

# Function to handle cleanup
cleanup() {
    echo "Stopping the streaming application..."
    pkill -f kvs_gstreamer_sample
    exit
}

# Ensure cleanup is called on exit
trap cleanup EXIT

cd /app/amazon-kinesis-video-streams-producer-sdk-cpp/build

while true; do 
    echo "Starting stream $STREAM_NAME with file $VIDEO_FILE"
    ./kvs_gstreamer_sample $STREAM_NAME /app/$VIDEO_FILE
    sleep 5
done