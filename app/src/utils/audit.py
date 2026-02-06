import json
from datetime import datetime, timezone

from infra.sqs.audit_queue import send_message


def publish_audit(feature, action, actor, old, new):
    payload = {
        "feature": feature,
        "action": action,
        "actor": actor,
        "old": old,
        "new": new,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    send_message(json.dumps(payload, default=str))
