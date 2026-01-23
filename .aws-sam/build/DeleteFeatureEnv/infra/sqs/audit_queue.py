import boto3
from infra.env import get_env

from infra.sqs.client import get_sqs_client

QUEUE_URL = get_env("AUDIT_QUEUE_URL")

if not QUEUE_URL:
    raise RuntimeError("AUDIT_QUEUE_URL env var not set")

_sqs = get_sqs_client()


def send_message(message_body: str):
    return _sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=message_body,
    )
