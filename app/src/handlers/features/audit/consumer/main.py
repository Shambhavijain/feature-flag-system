import json
import logging

from infra.dynamodb import table


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info("AuditConsumer Lambda invoked")
    logger.info(f"Records received: {len(event['Records'])}")
    
    batch_item_failures = []

    for record in event["Records"]:
        try:
            message = json.loads(record["body"])
            
            logger.info(
                f"Processing audit message | "
                f"feature={message['feature']} | "
                f"action={message['action']}"
            )
            
            table.put_item(
                Item={
                    "PK": f"AUDIT#{message['feature'].lower()}",
                    "SK": f"LOGS#{message['timestamp']}",
                    "action": message["action"],
                    "actor": message["actor"],
                    "old_value": message.get("old"),
                    "new_value": message.get("new"),
                }
            )
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            batch_item_failures.append({"itemIdentifier": record["messageId"]})
    
    return {"batchItemFailures": batch_item_failures}

