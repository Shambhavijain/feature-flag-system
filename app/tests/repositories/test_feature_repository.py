import unittest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError

from repository.feature_repository import FeatureRepository
from error_handling.exceptions import ConflictException, EnvironmentNotFoundException
from models.feature_model import FeatureMeta, FeatureEnv, AuditLog
from enums.enums import Environment


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
            environments={"dev": True},
        )

        self.mock_table.meta.client.transact_write_items.assert_called_once()

    def test_create_feature_conflict(self):
        self.mock_table.meta.client.transact_write_items.side_effect = ClientError(
            error_response={"Error": {"Code": "TransactionCanceledException"}},
            operation_name="TransactWriteItems",
        )

        with self.assertRaises(ConflictException):
            self.repo.create_feature(
                feature_name="NewFeature",
                description="test",
                environments={"dev": True},
            )

    def test_create_feature_unexpected_client_error(self):
        self.mock_table.meta.client.transact_write_items.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalServerError"}},
            operation_name="TransactWriteItems",
        )

        with self.assertRaises(ClientError):
            self.repo.create_feature(
                feature_name="NewFeature",
                description="test",
                environments={"dev": True},
            )

    def test_create_feature_multiple_environments(self):
        self.mock_table.meta.client.transact_write_items.return_value = {}

        self.repo.create_feature(
            feature_name="NewFeature",
            description="test",
            environments={"dev": True, "prod": False},
        )

        args = self.mock_table.meta.client.transact_write_items.call_args[1]
        transact_items = args["TransactItems"]

     
        self.assertEqual(len(transact_items), 3)

    def test_get_feature_details_found(self):
        self.mock_table.get_item.return_value = {
            "Item": {
                "PK": "FEATURES",
                "SK": "FEATURE#feature",
                "description": "desc",
                "created_at": 123,
            }
        }

        item = self.repo.get_feature_details("feature")

        self.assertIsInstance(item, FeatureMeta)
        self.assertEqual(item.name, "feature")
        self.assertEqual(item.description, "desc")

    def test_get_feature_details_not_found(self):
        self.mock_table.get_item.return_value = {}

        item = self.repo.get_feature_details("missing")

        self.assertIsNone(item)

    def test_get_feature_envs_success(self):
        self.mock_table.query.return_value = {
            "Items": [
                {
                    "SK": "ENV#dev",
                    "environment": "dev",
                    "enabled": True,
                    "rollout_end_at": None,
                    "updated_at": 1,
                },
                {
                    "SK": "ENV#prod",
                    "environment": "prod",
                    "enabled": False,
                    "rollout_end_at": None,
                    "updated_at": 2,
                },
            ]
        }

        envs = self.repo.get_feature_envs("feature")

        self.assertEqual(len(envs), 2)
        self.assertIsInstance(envs[0], FeatureEnv)
        self.assertEqual(envs[0].environment, Environment.DEV)

    def test_get_feature_envs_empty(self):
        self.mock_table.query.return_value = {}

        envs = self.repo.get_feature_envs("feature")

        self.assertEqual(envs, [])

    def test_get_env_found(self):
        self.mock_table.get_item.return_value = {
            "Item": {
                "environment": "dev",
                "enabled": True,
                "rollout_end_at": None,
                "updated_at": 1,
            }
        }

        env = self.repo.get_env("feature", "dev")

        self.assertIsInstance(env, FeatureEnv)
        self.assertTrue(env.enabled)
        self.assertEqual(env.environment, Environment.DEV)

    def test_get_env_not_found(self):
        self.mock_table.get_item.return_value = {}

        env = self.repo.get_env("feature", "dev")

        self.assertIsNone(env)

    def test_put_env_success(self):
        self.mock_table.update_item.return_value = {}

        self.repo.put_env(
            feature_name="feature",
            env="dev",
            enabled=True,
            rollout_end_at=None,
        )

        self.mock_table.update_item.assert_called_once()

    def test_put_env_not_found(self):
        self.mock_table.update_item.side_effect = ClientError(
            error_response={"Error": {"Code": "ConditionalCheckFailedException"}},
            operation_name="UpdateItem",
        )

        with self.assertRaises(EnvironmentNotFoundException):
            self.repo.put_env(
                feature_name="feature",
                env="dev",
                enabled=True,
                rollout_end_at=None,
            )

    def test_put_env_unexpected_client_error(self):
        self.mock_table.update_item.side_effect = ClientError(
            error_response={"Error": {"Code": "ProvisionedThroughputExceededException"}},
            operation_name="UpdateItem",
        )

        with self.assertRaises(ClientError):
            self.repo.put_env(
                feature_name="feature",
                env="dev",
                enabled=True,
                rollout_end_at=None,
            )

    def test_delete_env_not_found(self):
        self.mock_table.delete_item.side_effect = ClientError(
            error_response={"Error": {"Code": "ConditionalCheckFailedException"}},
            operation_name="DeleteItem",
        )

        with self.assertRaises(EnvironmentNotFoundException):
            self.repo.delete_env("feature", "prod")

    def test_delete_env_unexpected_client_error(self):
        self.mock_table.delete_item.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalServerError"}},
            operation_name="DeleteItem",
        )

        with self.assertRaises(ClientError):
            self.repo.delete_env("feature", "dev")

    

    def test_delete_feature_with_envs(self):
        self.mock_table.query.return_value = {
            "Items": [
                {"SK": "ENV#dev"},
                {"SK": "ENV#prod"},
            ]
        }

        self.repo.delete_feature("feature")

        args = self.mock_table.meta.client.transact_write_items.call_args[1]
        self.assertEqual(len(args["TransactItems"]), 3)

    def test_delete_feature_only_feature_exists(self):
        self.mock_table.query.return_value = {"Items": []}

        self.repo.delete_feature("feature")

        args = self.mock_table.meta.client.transact_write_items.call_args[1]
        self.assertEqual(len(args["TransactItems"]), 1)

    def test_get_audit_logs(self):
        self.mock_table.query.return_value = {
            "Items": [
                {
                    "action": "CREATE",
                    "actor": "admin",
                    "old": None,
                    "new": {},
                    "timestamp": 1,
                },
                {
                    "action": "DELETE",
                    "actor": "admin",
                    "old": {},
                    "new": None,
                    "timestamp": 2,
                },
            ]
        }

        logs = self.repo.get_audit_logs("feature")

        self.assertEqual(len(logs), 2)
        self.assertIsInstance(logs[0], AuditLog)

    def test_get_audit_logs_empty(self):
        self.mock_table.query.return_value = {"Items": []}

        logs = self.repo.get_audit_logs("feature")

        self.assertEqual(logs, [])

    def test_get_features_success(self):
        self.mock_table.query.return_value = {
            "Items": [
                {"SK": "FEATURE#f1", "description": "d1", "created_at": 1},
                {"SK": "FEATURE#f2", "description": "d2", "created_at": 2},
            ]
        }

        items = self.repo.get_features()

        self.assertEqual(len(items), 2)
        self.assertIsInstance(items[0], FeatureMeta)
        self.assertEqual(items[0].name, "f1")

    def test_get_features_empty(self):
        self.mock_table.query.return_value = {}

        items = self.repo.get_features()

        self.assertEqual(items, [])
