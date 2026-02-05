import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.features.audit.consumer.main import handler


class TestAuditConsumer(unittest.TestCase):

    @patch("src.handlers.features.audit.consumer.main.table")
    def test_audit_consumer_success_single_record(self, mock_table):
        event = {
                "Records": [
                {
                    "body": json.dumps({
                        "feature": "NewFeature",
                        "action": "CREATE",
                        "actor": "ADMIN",
                        "timestamp": "2026-01-01T10:00:00Z",
                        "old": None,
                        "new": {"enabled": True}
                    })
                }
            ]
        }

        handler(event, context={})

        mock_table.put_item.assert_called_once_with(
            Item={
                "PK": "AUDIT#newfeature",
                "SK": "LOGS#2026-01-01T10:00:00Z",
                "action": "CREATE",
                "actor": "ADMIN",
                "old_value": None,
                "new_value": {"enabled": True},
            }
        )


    @patch("src.handlers.features.audit.consumer.main.table")
    def test_audit_consumer_multiple_records(self, mock_table):
        event = {
            "Records": [
                {
                    "body": json.dumps({
                        "feature": "FeatureA",
                        "action": "UPDATE",
                        "actor": "ADMIN",
                        "timestamp": "t1"
                    })
                },
                {
                    "body": json.dumps({
                        "feature": "FeatureB",
                        "action": "DELETE",
                        "actor": "ADMIN",
                        "timestamp": "t2"
                    })
                }
            ]
        }

        handler(event, context={})

        self.assertEqual(mock_table.put_item.call_count, 2)
    
    @patch("src.handlers.features.audit.consumer.main.table")
    def test_audit_consumer_missing_optional_fields(self, mock_table):
        event = {
            "Records": [
                {
                    "body": json.dumps({
                        "feature": "Test",
                        "action": "UPDATE",
                        "actor": "ADMIN",
                        "timestamp": "t1"
                    })
                }
            ]
        }

        handler(event, context={})

        item = mock_table.put_item.call_args.kwargs["Item"]
        self.assertIsNone(item["old_value"])
        self.assertIsNone(item["new_value"])
    
    def test_audit_consumer_invalid_json(self):
        event = {
            "Records": [
                {"body": "{invalid-json"}
            ]
        }

        with self.assertRaises(json.JSONDecodeError):
            handler(event, context={})
