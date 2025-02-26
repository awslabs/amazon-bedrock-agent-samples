import boto3
from datetime import datetime
import random
import time
import os


def get_ddb_client():
    return boto3.client(
        "dynamodb",
        region_name=os.environ["AWS_DEFAULT_REGION"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
    )


def generate_sensor_data():
    temp = round(random.uniform(15, 21), 1)
    humidity = round(random.uniform(25, 45), 0)
    return str(temp), str(humidity)


def get_formatted_timestamp():
    return datetime.now().strftime("%Y%m%d%H%M%S")


def write_to_dynamodb(client, room):
    temp, humidity = generate_sensor_data()
    timestamp = get_formatted_timestamp()

    try:
        client.put_item(
            TableName=os.environ["DYNAMODB_TABLE"],  # Now reading from environment
            Item={
                "pk": {"S": room},
                "sk": {"S": timestamp},
                "temp": {"S": temp},
                "humidity": {"S": humidity},
            },
        )
        print(f"Written data for {room}: temp={temp}, humidity={humidity}")
    except Exception as e:
        print(f"Error writing to DynamoDB: {str(e)}")


def main():
    client = get_ddb_client()
    rooms = ["guestroom", "pannrum"]

    while True:
        for room in rooms:
            write_to_dynamodb(client, room)
        time.sleep(60)  # Wait for 1 minute


if __name__ == "__main__":
    main()
