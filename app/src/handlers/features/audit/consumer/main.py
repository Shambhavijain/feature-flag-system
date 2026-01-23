import json
import logging

from infra.dynamodb import table


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info("AuditConsumer Lambda invoked")
    logger.info(f"Records received: {len(event['Records'])}")

    for record in event["Records"]:
        message = json.loads(record["body"])

        logger.info(
            f"Processing audit message | "
            f"feature={message['feature']} | "
            f"action={message['action']}"
        )

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
