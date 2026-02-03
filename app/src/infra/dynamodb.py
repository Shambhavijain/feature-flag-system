import boto3

from infra.config import get_env

dynamodb = boto3.resource(
    "dynamodb",
    region_name=get_env("AWS_REGION", "us-east-1"),
)
table = dynamodb.Table(get_env("DDB_TABLE_NAME"))
