from infra.dynamodb import table
from datetime import datetime, timezone

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
                "ConditionExpression": "attribute_not_exists(PK)",
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

        self.table.meta.client.transact_write_items(
            TransactItems=transact_items
        )



    def put_env(self, feature_name: str, env: str, enabled: bool, rollout_end_at: str | None):
        feature_name = feature_name.lower()
        env = env.lower()
        self.table.put_item(
            Item={
                "PK": f"FEATURE#{feature_name}",
                "SK": f"ENV#{env}",
                "enabled": enabled,
                "environment": env,
                "rollout_end_at": rollout_end_at,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
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
        env = env.lower()
        self.table.delete_item(
            Key={
                "PK": f"FEATURE#{feature_name}",
                "SK": f"ENV#{env}"
            }
        )

   
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
    def get_feature(self, feature_name: str):
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