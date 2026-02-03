import unittest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError

from repository.feature_repository import FeatureRepository
from error_handling.exceptions import ConflictException, EnvironmentNotFoundException


class TestFeatureRepository(unittest.TestCase):

    def setUp(self):
        self.mock_table = MagicMock()
        self.mock_table.name = "FeatureTable"
        self.mock_table.meta.client.transact_write_items = MagicMock()

        self.repo = FeatureRepository(self.mock_table)

    def test_create_feature_success(self):
        self.mock_table.meta.client.transact_write_items.return_value = {}

        self.repo.create_feature(
            feature_name="NewFeature",
            description="test",
            environments={"dev": True}
        )

        self.mock_table.meta.client.transact_write_items.assert_called_once()

    def test_create_feature_conflict(self):
        self.mock_table.meta.client.transact_write_items.side_effect = ClientError(
            error_response={
                "Error": {"Code": "TransactionCanceledException"}
            },
            operation_name="TransactWriteItems"
        )

        with self.assertRaises(ConflictException):
            self.repo.create_feature(
                feature_name="NewFeature",
                description="test",
                environments={"dev": True}
            )

    def test_create_feature_unexpected_client_error(self):
        self.mock_table.meta.client.transact_write_items.side_effect = ClientError(
            error_response={
                "Error": {"Code": "InternalServerError"}
            },
            operation_name="TransactWriteItems"
        )

        with self.assertRaises(ClientError):
            self.repo.create_feature(
                feature_name="NewFeature",
                description="test",
                environments={"dev": True}
            )        

    def test_get_env_found(self):
        self.mock_table.get_item.return_value = {
            "Item": {
                "environment": "dev",
                "enabled": True
            }
        }

        env = self.repo.get_env("feature", "dev")

        self.assertIsNotNone(env)
        self.assertTrue(env["enabled"])

    def test_put_env_success(self):
        self.mock_table.update_item.return_value = {}

        self.repo.put_env(
            feature_name="feature",
            env="dev",
            enabled=True,
            rollout_end_at=None
        )

        self.mock_table.update_item.assert_called_once()
    
    def test_put_env_not_found(self):
        self.mock_table.update_item.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ConditionalCheckFailedException"}
            },
            operation_name="UpdateItem"
        )

        with self.assertRaises(EnvironmentNotFoundException):
            self.repo.put_env(
                feature_name="feature",
                env="dev",
                enabled=True,
                rollout_end_at=None
            )

    def test_put_env_unexpected_client_error(self):
        self.mock_table.update_item.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ProvisionedThroughputExceededException"}
            },
            operation_name="UpdateItem"
        )

        with self.assertRaises(ClientError):
            self.repo.put_env(
                feature_name="feature",
                env="dev",
                enabled=True,
                rollout_end_at=None
            )
        

    def test_delete_env_not_found(self):
        self.mock_table.delete_item.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ConditionalCheckFailedException"}
            },
            operation_name="DeleteItem"
        )

        with self.assertRaises(EnvironmentNotFoundException):
            self.repo.delete_env("feature", "prod")
    def test_delete_env_unexpected_client_error(self):
        self.mock_table.delete_item.side_effect = ClientError(
            error_response={
                "Error": {"Code": "InternalServerError"}
            },
            operation_name="DeleteItem"
        )

        with self.assertRaises(ClientError):
            self.repo.delete_env("feature", "dev")
        
    def test_get_feature_items(self):
        self.mock_table.query.return_value = {
            "Items": [{"SK": "META"}, {"SK": "ENV#dev"}]
        }

        items = self.repo.get_feature_items("feature")

        self.assertEqual(len(items), 2)
    def test_delete_feature_skips_audit_items(self):
        self.mock_table.query.return_value = {
            "Items": [
                {"PK": "FEATURE#f1", "SK": "META"},
                {"PK": "FEATURE#f1", "SK": "ENV#dev"},
                {"PK": "FEATURE#f1", "SK": "AUDIT#123"},
            ]
        }

        mock_batch = MagicMock()
        self.mock_table.batch_writer.return_value.__enter__.return_value = mock_batch

        self.repo.delete_feature("f1")

        self.assertEqual(mock_batch.delete_item.call_count, 2)
    def test_get_audit_logs(self):
        self.mock_table.query.return_value = {
            "Items": [{"SK": "AUDIT#1"}, {"SK": "AUDIT#2"}]
        }

        logs = self.repo.get_audit_logs("feature")

        self.assertEqual(len(logs), 2)
    def test_list_features_success(self):
        self.mock_table.scan.return_value = {
            "Items": [
                {
                    "PK": "FEATURE#f1",
                    "SK": "META",
                    "description": "desc1",
                    "created_at": "2026-01-01T00:00:00Z"
                },
                {
                    "PK": "FEATURE#f2",
                    "SK": "META",
                    "description": "desc2",
                    "created_at": "2026-01-02T00:00:00Z"
                }
            ]
        }

        items = self.repo.list_features()

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["SK"], "META")
        self.mock_table.scan.assert_called_once()
    
    def test_list_features_empty(self):
        self.mock_table.scan.return_value = {}

        items = self.repo.list_features()

        self.assertEqual(items, [])
        self.mock_table.scan.assert_called_once()

