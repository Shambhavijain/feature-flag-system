import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from services.feature_service import FeatureService
from dto.feature_dto import CreateFeatureDTO, UpdateFeatureEnvDTO, EvaluateDTO, FeatureListItemDTO
from error_handling.exceptions import (
    FeatureNotFoundException,
    EnvironmentNotFoundException,
)
from enums.enums import Environment
from models.feature_model import FeatureMeta, FeatureEnv, AuditLog


class TestFeatureService(unittest.TestCase):

    def setUp(self):
        self.repo = MagicMock()
        self.service = FeatureService(self.repo)

    

    @patch("services.feature_service.publish_audit")
    def test_create_feature_success(self, mock_audit):
        req = CreateFeatureDTO(
            name="TestFeature",
            description="desc",
            environments={"dev": True},
        )

        self.service.create_feature(req, actor="admin")

        self.repo.create_feature.assert_called_once_with(
            "testfeature",
            "desc",
            {"dev": True},
        )
        mock_audit.assert_called_once()

    def test_create_feature_repo_error(self):
        req = CreateFeatureDTO(
            name="TestFeature",
            description="desc",
            environments={"dev": True},
        )

        self.repo.create_feature.side_effect = Exception("boom")

        with self.assertRaises(Exception):
            self.service.create_feature(req, actor="admin")

    

    def test_get_feature_success(self):
        meta = FeatureMeta(
            name="feature",
            description="desc",
            created_at=1,
        )

        env = FeatureEnv(
            feature_name="feature",
            environment=Environment.DEV,
            enabled=True,
            rollout_end_at=None,
            updated_at=1,
        )

        self.repo.get_feature_details.return_value = meta
        self.repo.get_feature_envs.return_value = [env]

        result = self.service.get_feature("feature")

        self.assertEqual(result.meta.name, "feature")
        self.assertEqual(result.environments[Environment.DEV].enabled, True)

    def test_get_feature_not_found(self):
        self.repo.get_feature_details.return_value = None

        with self.assertRaises(FeatureNotFoundException):
            self.service.get_feature("feature")

    

    @patch("services.feature_service.publish_audit")
    @patch("services.feature_service.map_env_for_audit")
    def test_remove_env_success(self, mock_map, mock_audit):
        env = FeatureEnv(
            feature_name="feature",
            environment=Environment.DEV,
            enabled=True,
            rollout_end_at=None,
            updated_at=1,
        )

        self.repo.get_env.return_value = env
        mock_map.return_value = {"environment": "dev"}

        self.service.remove_env("feature", "dev", "admin")

        self.repo.delete_env.assert_called_once_with("feature", "dev")
        mock_audit.assert_called_once()

    def test_remove_env_not_found(self):
        self.repo.get_env.return_value = None

        with self.assertRaises(EnvironmentNotFoundException):
            self.service.remove_env("feature", "dev", "admin")

    

    @patch("services.feature_service.publish_audit")
    def test_evaluate_auto_rollout(self, mock_audit):
        past_time = int(
            (datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp()
        )

        meta = FeatureMeta("feature", "desc", 1)
        env = FeatureEnv(
            feature_name="feature",
            environment=Environment.DEV,
            enabled=False,
            rollout_end_at=past_time,
            updated_at=1,
        )

        self.repo.get_feature_details.return_value = meta
        self.repo.get_env.return_value = env

        req = EvaluateDTO(
            feature="feature",
            environment=Environment.DEV,
        )

        result = self.service.evaluate(req)

        self.assertTrue(result)
        self.repo.put_env.assert_called_once()
        mock_audit.assert_called_once()

    def test_evaluate_no_rollout(self):
        meta = FeatureMeta("feature", "desc", 1)
        env = FeatureEnv(
            feature_name="feature",
            environment=Environment.DEV,
            enabled=True,
            rollout_end_at=None,
            updated_at=1,
        )

        self.repo.get_feature_details.return_value = meta
        self.repo.get_env.return_value = env

        req = EvaluateDTO(
            feature="feature",
            environment=Environment.DEV,
        )

        result = self.service.evaluate(req)

        self.assertTrue(result)
        self.repo.put_env.assert_not_called()

    def test_evaluate_rollout_not_expired(self):
        future_time = int(
            (datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()
        )

        meta = FeatureMeta("feature", "desc", 1)
        env = FeatureEnv(
            feature_name="feature",
            environment=Environment.DEV,
            enabled=False,
            rollout_end_at=future_time,
            updated_at=1,
        )

        self.repo.get_feature_details.return_value = meta
        self.repo.get_env.return_value = env

        req = EvaluateDTO(
            feature="feature",
            environment=Environment.DEV,
        )

        result = self.service.evaluate(req)

        self.assertFalse(result)
        self.repo.put_env.assert_not_called()

    def test_evaluate_feature_not_found(self):
        self.repo.get_feature_details.return_value = None

        req = EvaluateDTO(
            feature="feature",
            environment=Environment.DEV,
        )

        with self.assertRaises(FeatureNotFoundException):
            self.service.evaluate(req)

    def test_evaluate_env_not_found(self):
        meta = FeatureMeta("feature", "desc", 1)
        self.repo.get_feature_details.return_value = meta
        self.repo.get_env.return_value = None

        req = EvaluateDTO(
            feature="feature",
            environment=Environment.DEV,
        )

        with self.assertRaises(EnvironmentNotFoundException):
            self.service.evaluate(req)

    @patch("services.feature_service.publish_audit")
    @patch("services.feature_service.map_env_for_audit")
    def test_update_env_success(self, mock_map, mock_audit):
        env = FeatureEnv(
            feature_name="feature",
            environment=Environment.DEV,
            enabled=False,
            rollout_end_at=None,
            updated_at=1,
        )

        self.repo.get_env.return_value = env
        mock_map.return_value = {"environment": "dev"}

        req = UpdateFeatureEnvDTO(
            enabled=True,
            rollout_end_at=None,
        )

        self.service.update_env("feature", "dev", req, actor="admin")

        self.repo.put_env.assert_called_once()
        mock_audit.assert_called_once()

    def test_update_env_not_found(self):
        self.repo.get_env.return_value = None

        req = UpdateFeatureEnvDTO(enabled=True, rollout_end_at=None)

        with self.assertRaises(EnvironmentNotFoundException):
            self.service.update_env("feature", "dev", req, actor="admin")

    @patch("services.feature_service.publish_audit")
    def test_delete_feature_success(self, mock_audit):
        meta = FeatureMeta("feature", "desc", 1)
        self.repo.get_feature_details.return_value = meta
        self.repo.get_feature_envs.return_value = []

        self.service.delete_feature("feature", actor="admin")

        self.repo.delete_feature.assert_called_once_with("feature")
        mock_audit.assert_called_once()

    def test_delete_feature_not_found(self):
        self.repo.get_feature_details.return_value = None

        with self.assertRaises(FeatureNotFoundException):
            self.service.delete_feature("feature", actor="admin")

    @patch("services.feature_service.map_audit_items")
    def test_get_audit_logs(self, mock_mapper):
        logs = [
            AuditLog("CREATE", "admin", None, {}, 1),
        ]
        self.repo.get_audit_logs.return_value = logs
        mock_mapper.return_value = [{"action": "CREATE"}]

        result = self.service.get_audit_logs("feature")

        self.repo.get_audit_logs.assert_called_once_with("feature")
        mock_mapper.assert_called_once_with(logs)
        self.assertEqual(result, [{"action": "CREATE"}])


    def test_list_features_success(self):
        features = [
            FeatureListItemDTO(
                name="feature1",
                description="description1",
                created_at=12789563,
            ),
            FeatureListItemDTO(
                name="feature2",
                description="description2",
                created_at=12985376,
            ),
        ]

        self.repo.get_features.return_value = features

        result = self.service.list_features()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "feature1")
        self.assertEqual(result[1].name, "feature2")

    def test_list_features_empty(self):
        self.repo.get_features.return_value = []

        result = self.service.list_features()

        self.assertEqual(result, [])
