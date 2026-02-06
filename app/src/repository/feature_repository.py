from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone

from error_handling.exceptions import (
    ConflictException,
    EnvironmentNotFoundException,
)


class FeatureRepository:
    def __init__(self, table):
        self.table = table

    def create_feature(
        self,
        feature_name: str,
        description: str,
        environments: dict[str, bool],
    ):
        feature_name = feature_name.lower()
        now = int(datetime.now(timezone.utc).timestamp())

        transact_items = []

        transact_items.append({
            "Put": {
                "TableName": self.table.name,
                "Item": {
                    "PK": "FEATURES",
                    "SK": f"FEATURE#{feature_name}",
                    "description": description,
                    "created_at": now,
                },
                
                "ConditionExpression": "attribute_not_exists(PK)",
            }
        })

        for env, enabled in environments.items():
            transact_items.append({
                "Put": {
                    "TableName": self.table.name,
                    "Item": {
                        "PK": f"ENVIRONMENT#{feature_name}",
                        "SK": f"ENV#{env.lower()}",
                        "environment": env.lower(),
                        "enabled": enabled,
                        "rollout_end_at": None,
                        "updated_at": now,
                    },
                    "ConditionExpression": "attribute_not_exists(SK)",
                }
            })

        try:
            self.table.meta.client.transact_write_items(
                TransactItems=transact_items
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "TransactionCanceledException":
                raise ConflictException("Feature already exists")
            raise

    def put_env(
        self,
        feature_name: str,
        env: str,
        enabled: bool,
        rollout_end_at: str | None,
    ):
        feature_name = feature_name.lower()
        env = env.lower()

        try:
            self.table.update_item(
                Key={
                    "PK": f"ENVIRONMENT#{feature_name}",
                    "SK": f"ENV#{env}",
                },
                UpdateExpression="""
                    SET enabled = :enabled,
                        rollout_end_at = :rollout,
                        updated_at = :updated
                """,
                ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
                ExpressionAttributeValues={
                    ":enabled": enabled,
                    ":rollout": rollout_end_at,
                    ":updated": int(datetime.now(timezone.utc).timestamp()),
                },
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise EnvironmentNotFoundException(feature_name, env)
            raise

    def get_env(self, feature_name: str, env: str):
        response = self.table.get_item(
            Key={
                "PK": f"ENVIRONMENT#{feature_name.lower()}",
                "SK": f"ENV#{env.lower()}",
            }
        )
        return response.get("Item")

    def delete_env(self, feature_name: str, env: str):
        try:
            self.table.delete_item(
                Key={
                    "PK": f"ENVIRONMENT#{feature_name.lower()}",
                    "SK": f"ENV#{env.lower()}",
                },
                ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise EnvironmentNotFoundException(feature_name, env)
            raise

    def delete_feature(self, feature_name: str):
        feature_name = feature_name.lower()

        transact_items = [
            {
                "Delete": {
                    "TableName": self.table.name,
                    "Key": {
                        "PK": "FEATURES",
                        "SK": f"FEATURE#{feature_name}",
                    },
                    "ConditionExpression": "attribute_exists(PK)",
                }
            }
        ]

        response = self.table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={
                ":pk": f"ENVIRONMENT#{feature_name}",
            },
        )

        for item in response.get("Items", []):
            transact_items.append({
                "Delete": {
                    "TableName": self.table.name,
                    "Key": {
                        "PK": item["PK"],
                        "SK": item["SK"],
                    },
                    "ConditionExpression": "attribute_exists(PK)",
                }
            })

        self.table.meta.client.transact_write_items(
            TransactItems=transact_items
        )

    def get_audit_logs(self, feature_name: str):
        feature_name = feature_name.lower()

        response = self.table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
            ExpressionAttributeValues={
                ":pk": f"AUDIT#{feature_name}",
                ":sk": "LOGS#",
            },
        )
        return response.get("Items", [])

    def list_features(self):
        response = self.table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={
                ":pk": "FEATURES",
            },
        )
        return response.get("Items", [])
    
    def get_feature_details(self, feature_name: str) -> dict | None:
        feature_name = feature_name.lower()

        response = self.table.get_item(
            Key={
                "PK": "FEATURES",
                "SK": f"FEATURE#{feature_name}",
            }
        )

        return response.get("Item")


    def get_feature_envs(self, feature_name: str) -> list[dict]:
        feature_name = feature_name.lower()

        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(
                f"ENVIRONMENT#{feature_name}"
            )
        )

        return response.get("Items", [])

