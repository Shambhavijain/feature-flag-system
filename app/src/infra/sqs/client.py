import boto3
from infra.config import get_env


_sqs_client = None


def get_sqs_client():
    global _sqs_client
    if _sqs_client is None:
        _sqs_client = boto3.client(
            "sqs",
            region_name=get_env("AWS_REGION", "us-east-1"),
          
        )
    return _sqs_client
