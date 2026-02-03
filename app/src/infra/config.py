import os
import json
import boto3

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


_cached_secrets = None

def _load_secrets():
    global _cached_secrets

    if _cached_secrets:
        return _cached_secrets

    secret_arn = os.getenv("JWT_SECRET_ARN")
    if not secret_arn:
        return {}

    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_arn)
    _cached_secrets = json.loads(response["SecretString"])

    return _cached_secrets

def get_env(key: str, default=None):
    value = os.getenv(key)
    if value is not None:
        return value

    secrets = _load_secrets()
    if key in secrets:
        return secrets[key]

    if default is not None:
        return default

    raise RuntimeError(f"Missing required env variable: {key}")
