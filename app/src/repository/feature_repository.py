from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone

from error_handling.exceptions import (
    ConflictException,
    EnvironmentNotFoundException,
)
from models.feature_model import FeatureMeta, FeatureEnv, AuditLog
from enums.enums import Environment


class FeatureRepository:
    def __init__(self, table):
        self.table = table


    def create_feature(
        self,
        feature_name: str,
        description: str,
        environments: dict[str, bool],
    ) -> None:
        feature_name = feature_name.lower()
        now = int(datetime.now(timezone.utc).timestamp())

        transact_items = [
            {
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
            }
        ]

        for env, enabled in environments.items():
            env = env.lower()
            transact_items.append(
                {
                    "Put": {
                        "TableName": self.table.name,
                        "Item": {
                            "PK": f"ENVIRONMENT#{feature_name}",
                            "SK": f"ENV#{env}",
                            "environment": env,
                            "enabled": enabled,
                            "rollout_end_at": None,
                            "updated_at": now,
                        },
                        "ConditionExpression": "attribute_not_exists(SK)",
                    }
                }
            )

        try:
            self.table.meta.client.transact_write_items(
                TransactItems=transact_items
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "TransactionCanceledException":
                raise ConflictException("Feature already exists")
            raise


    def get_feature_details(self, feature_name: str) -> FeatureMeta | None:
        feature_name = feature_name.lower()

        response = self.table.get_item(
            Key={
                "PK": "FEATURES",
                "SK": f"FEATURE#{feature_name}",
            }
        )

        item = response.get("Item")
        if not item:
            return None

        return FeatureMeta(
            name=feature_name,
            description=item.get("description"),
            created_at=item["created_at"],
        )


    def get_features(self) -> list[FeatureMeta]:
        response = self.table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": "FEATURES"},
        )

        items = response.get("Items", [])
        features: list[FeatureMeta] = []

        for item in items:
            features.append(
                FeatureMeta(
                    name=item["SK"].replace("FEATURE#", ""),
                    description=item.get("description"),
                    created_at=item["created_at"],
                )
            )

        return features


    def get_feature_envs(self, feature_name: str) -> list[FeatureEnv]:
        feature_name = feature_name.lower()

        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(
                f"ENVIRONMENT#{feature_name}"
            )
        )

        envs: list[FeatureEnv] = []

        for item in response.get("Items", []):
            envs.append(
                FeatureEnv(
                    feature_name=feature_name,
                    environment=Environment[item["environment"].upper()],
                    enabled=item["enabled"],
                    rollout_end_at=item.get("rollout_end_at"),
                    updated_at=item["updated_at"],
                )
            )

        return envs

    def get_env(self, feature_name: str, env: str) -> FeatureEnv | None:
        feature_name = feature_name.lower()
        env = env.lower()

        response = self.table.get_item(
            Key={
                "PK": f"ENVIRONMENT#{feature_name}",
                "SK": f"ENV#{env}",
            }
        )

        item = response.get("Item")
        if not item:
            return None

        return FeatureEnv(
            feature_name=feature_name,
            environment=Environment[item["environment"].upper()],
            enabled=item["enabled"],
            rollout_end_at=item.get("rollout_end_at"),
            updated_at=item["updated_at"],
        )


    def put_env(
        self,
        feature_name: str,
        env: str,
        enabled: bool,
        rollout_end_at: int | None,
    ) -> None:
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

    def delete_env(self, feature_name: str, env: str) -> None:
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


    def delete_feature(self, feature_name: str) -> None:
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
            transact_items.append(
                {
                    "Delete": {
                        "TableName": self.table.name,
                        "Key": {
                            "PK": f"ENVIRONMENT#{feature_name}",
                            "SK": item["SK"],
                        },
                        "ConditionExpression": "attribute_exists(PK)",
                    }
                }
            )

        self.table.meta.client.transact_write_items(
            TransactItems=transact_items
        )


    def get_audit_logs(self, feature_name: str) -> list[AuditLog]:
        response = self.table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={
                ":pk": f"AUDIT#{feature_name.lower()}",
            },
        )

        logs: list[AuditLog] = []

        for item in response.get("Items", []):
            logs.append(
                AuditLog(
                    action=item["action"],
                    actor=item["actor"],
                    old=item.get("old"),
                    new=item.get("new"),
                    timestamp=item["timestamp"],
                )
            )

        return logs
