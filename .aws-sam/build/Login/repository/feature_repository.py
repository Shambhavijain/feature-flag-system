from botocore.exceptions import ClientError
from datetime import datetime, timezone

from infra.dynamodb import table
from error_handling.exceptions import ConflictException


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
        now = datetime.now(timezone.utc).isoformat()

        transact_items = []

        transact_items.append({
            "Put": {
                "TableName": self.table.name,
                "Item": {
                    "PK": f"FEATURE#{feature_name}",
                    "SK": "META",
                    "description": description,
                    "created_at": now,
                },
                "ConditionExpression": "attribute_not_exists(SK)",
            }
        })

        for env, enabled in environments.items():
            transact_items.append({
                "Put": {
                    "TableName": self.table.name,
                    "Item": {
                        "PK": f"FEATURE#{feature_name}",
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



    def put_env(self, feature_name: str, env: str, enabled: bool, rollout_end_at: str | None):
        feature_name = feature_name.lower()
        env = env.lower()
        self.table.update_item(
            Key={
                "PK": f"FEATURE#{feature_name}",
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
                ":updated": datetime.now(timezone.utc).isoformat(),
            },
        )


    def get_env(self, feature_name: str, env: str):
        feature_name = feature_name.lower()
        response = self.table.get_item(
            Key={
                "PK": f"FEATURE#{feature_name}",
                "SK": f"ENV#{env}"
            }
        )
        return response.get("Item")

    def delete_env(self, feature_name: str, env: str):
        feature_name = feature_name.lower()
        try:
            self.table.delete_item(
                Key={
                    "PK": f"FEATURE#{feature_name}",
                    "SK": f"ENV#{env}",
                },
                ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise EnvironmentNotFoundException(feature_name, env)
            raise

   
    def delete_feature(self, feature_name: str):
        feature_name=feature_name.lower()
        pk = f"FEATURE#{feature_name}"

        response = self.table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": pk},
        )

        items = response.get("Items", [])

        with self.table.batch_writer() as batch:
            for item in items:
                if item["SK"].startswith("AUDIT#"):
                    continue
                batch.delete_item(
                    Key={
                        "PK": item["PK"],
                        "SK": item["SK"],
                    }
                )
    def get_feature_items(self, feature_name: str):
        feature_name = feature_name.lower()
        pk = f"FEATURE#{feature_name}"
        response = self.table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": pk},
        )
        return response.get("Items", [])

    def get_audit_logs(self, feature_name: str):
        feature_name = feature_name.lower()
        pk = f"FEATURE#{feature_name}"
        response = self.table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :audit)",
            ExpressionAttributeValues={
                ":pk": pk,
                ":audit": "AUDIT#",
            },
        )
        return response.get("Items", [])            