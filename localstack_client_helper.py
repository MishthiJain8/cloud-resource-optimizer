# localstack_client.py
import boto3

LOCALSTACK_ENDPOINT = "http://localhost:4566"

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=LOCALSTACK_ENDPOINT,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1"
    )
