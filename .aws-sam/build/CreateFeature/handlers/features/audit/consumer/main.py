import json
from infra.dynamodb import table


def handler(event, context):
    for record in event["Records"]:
        message = json.loads(record["body"])

        table.put_item(
            Item={
                "PK": f"FEATURE#{message['feature'].lower()}",
                "SK": f"AUDIT#{message['timestamp']}",
                "action": message["action"],
                "actor": message["actor"],
                "old_value": message.get("old"),
                "new_value": message.get("new"),
                "created_at": message["timestamp"],
            }
        )
