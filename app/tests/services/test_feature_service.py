import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from services.feature_service import FeatureService
from dto.feature_dto import CreateFeatureDTO, UpdateFeatureEnvDTO, EvaluateDTO
from error_handling.exceptions import (
    FeatureNotFoundException,
    EnvironmentNotFoundException,
)
from constants.enums import Environment

class TestFeatureService(unittest.TestCase):

    def setUp(self):
        self.repo = MagicMock()
        self.service = FeatureService(self.repo)

    @patch("services.feature_service.publish_audit")
    def test_create_feature_success(self, mock_audit):
        req = CreateFeatureDTO(
            name="TestFeature",
            description="desc",
            environments={"dev": True}
        )

        self.service.create_feature(req, actor="admin")

        self.repo.create_feature.assert_called_once()
        mock_audit.assert_called_once()
   
    def test_create_feature_conflict(self):
        req = CreateFeatureDTO(
            name="TestFeature",
            description="desc",
            environments={"dev": True}
        )

        self.repo.create_feature.side_effect = Exception("boom")

        with self.assertRaises(Exception):
            self.service.create_feature(req, actor="admin")

    @patch("services.feature_service.map_feature_items")
    def test_get_feature_success(self, mock_mapper):
        self.repo.get_feature_items.return_value = [
            {"SK": "META", "name": "feature"}
        ]
        mock_mapper.return_value = {"name": "feature"}

        result = self.service.get_feature("feature")

        self.repo.get_feature_items.assert_called_once_with("feature")
        mock_mapper.assert_called_once()
        self.assertEqual(result, {"name": "feature"})

    def test_get_feature_not_found(self):
        self.repo.get_feature_items.return_value = []

        with self.assertRaises(FeatureNotFoundException):
            self.service.get_feature("feature")

    
    @patch("services.feature_service.publish_audit")
    @patch("services.feature_service.map_env_for_audit")
    def test_remove_env_success(self, mock_map, mock_audit):
        env_item = {"environment": "dev", "enabled": True}
        self.repo.get_env.return_value = env_item
        mock_map.return_value = env_item

        self.service.remove_env("feature", "dev", "admin")

        self.repo.delete_env.assert_called_once()
        mock_audit.assert_called_once()
    
    def test_remove_env_not_found(self):
        self.repo.get_env.return_value = None

        with self.assertRaises(EnvironmentNotFoundException):
            self.service.remove_env("feature", "dev", "admin")
   
    @patch("services.feature_service.publish_audit")
    def test_evaluate_auto_rollout(self, mock_audit):
        rollout_time = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

        self.repo.get_feature_items.return_value = [{"SK": "META"}]
        self.repo.get_env.return_value = {
            "enabled": False,
            "rollout_end_at": rollout_time,
            "environment": "dev",
        }

        req = EvaluateDTO(
            feature="feature",
            environment=Environment.DEV,
        )

        result = self.service.evaluate(req)

        self.assertTrue(result)
        self.repo.put_env.assert_called_once()
        mock_audit.assert_called_once()
     
    def test_evaluate_feature_not_found(self):
        self.repo.get_feature_items.return_value = []

        req = EvaluateDTO(
            feature="feature",
            environment=Environment.DEV,
            context={}
        )

        with self.assertRaises(FeatureNotFoundException):
            self.service.evaluate(req)

    def test_evaluate_feature_not_found(self):
        self.repo.get_feature_items.return_value = []

        req = EvaluateDTO(
            feature="feature",
            environment=Environment.DEV,
            context={}
        )

        with self.assertRaises(FeatureNotFoundException):
            self.service.evaluate(req)

    def test_evaluate_rollout_not_expired(self):
        future_time = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

        self.repo.get_feature_items.return_value = [{"SK": "META"}]
        self.repo.get_env.return_value = {
            "enabled": False,
            "rollout_end_at": future_time,
            "environment": "dev",
        }

        req = EvaluateDTO(
            feature="feature",
            environment=Environment.DEV,
            context={}
        )

        result = self.service.evaluate(req)

        self.assertFalse(result)
        self.repo.put_env.assert_not_called()
    
    def test_evaluate_no_rollout(self):
        self.repo.get_feature_items.return_value = [{"SK": "META"}]
        self.repo.get_env.return_value = {
            "enabled": True,
            "rollout_end_at": None,
            "environment": "dev",
        }

        req = EvaluateDTO(
            feature="feature",
            environment=Environment.DEV,
            context={}
        )

        result = self.service.evaluate(req)

        self.assertTrue(result)
   
    def test_evaluate_rollout_expired_already_enabled(self):
        past_time = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

        self.repo.get_feature_items.return_value = [{"SK": "META"}]
        self.repo.get_env.return_value = {
            "enabled": True,
            "rollout_end_at": past_time,
            "environment": "dev",
        }

        req = EvaluateDTO(
            feature="feature",
            environment=Environment.DEV,
            context={}
        )

        result = self.service.evaluate(req)

        self.assertTrue(result)
        self.repo.put_env.assert_not_called()


    @patch("services.feature_service.publish_audit")
    @patch("services.feature_service.map_env_for_audit")
    def test_update_env_success(self, mock_map, mock_audit):
        self.repo.get_env.return_value = {
            "environment": "dev",
            "enabled": False,
        }

        req = UpdateFeatureEnvDTO(
            enabled=True,
            rollout_end_at=None,
        )

        self.service.update_env(
            "feature",
            "dev",
            req,
            actor="admin"
        )

        self.repo.put_env.assert_called_once()
        mock_audit.assert_called_once()
    def test_evaluate_env_not_found(self):
        self.repo.get_feature_items.return_value = [{"SK": "META"}]
        self.repo.get_env.return_value = None

        req = EvaluateDTO(
            feature="feature",
            environment=Environment.DEV,
            context={}
        )

        with self.assertRaises(EnvironmentNotFoundException):
            self.service.evaluate(req)
     
    @patch("services.feature_service.publish_audit")
    @patch("services.feature_service.map_feature_items")
    def test_delete_feature_success(self, mock_mapper, mock_audit):
        self.repo.get_feature_items.return_value = [{"SK": "META"}]
        mock_mapper.return_value = {"feature": "feature"}

        self.service.delete_feature("feature", actor="admin")

        self.repo.delete_feature.assert_called_once_with("feature")
        mock_audit.assert_called_once()
 

    def test_delete_feature_not_found(self):
        self.repo.get_feature_items.return_value = []

        with self.assertRaises(FeatureNotFoundException):
            self.service.delete_feature("feature", actor="admin")
    
    @patch("services.feature_service.map_audit_items")
    def test_get_audit_logs(self, mock_mapper):
        self.repo.get_audit_logs.return_value = [{"SK": "AUDIT#1"}]
        mock_mapper.return_value = [{"action": "CREATE"}]

        result = self.service.get_audit_logs("feature")

        self.repo.get_audit_logs.assert_called_once_with("feature")
        mock_mapper.assert_called_once()
        self.assertEqual(result, [{"action": "CREATE"}])
    
    def test_update_env_not_found(self):
        self.repo.get_env.return_value = None

        req = UpdateFeatureEnvDTO(enabled=True, rollout_end_at=None)

        with self.assertRaises(EnvironmentNotFoundException):
            self.service.update_env("feature", "dev", req, actor="admin")
    
    def test_evaluate_env_not_found(self):
        self.repo.get_feature_items.return_value = [{"SK": "META"}]
        self.repo.get_env.return_value = None

        req = EvaluateDTO(
            feature="feature",
            environment=Environment.DEV,
            context={}
        )

        with self.assertRaises(EnvironmentNotFoundException):
            self.service.evaluate(req)
