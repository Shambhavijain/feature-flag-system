import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.features.delete_feature_env.main import (
    delete_feature_env_handler
)
from error_handling.exceptions import AppException


class TestDeleteFeatureEnvHandler(unittest.TestCase):

    def setUp(self):
        self.get_user_patcher = patch(
            "src.handlers.features.delete_feature_env.main.get_current_user"
        )
        self.require_admin_patcher = patch(
            "src.handlers.features.delete_feature_env.main.require_admin"
        )
        self.get_service_patcher = patch(
            "src.handlers.features.delete_feature_env.main.get_feature_service"
        )

        self.mock_get_user = self.get_user_patcher.start()
        self.mock_require_admin = self.require_admin_patcher.start()
        self.mock_get_service = self.get_service_patcher.start()

        self.mock_get_user.return_value = {"role": "ADMIN"}
        self.mock_require_admin.return_value = None

        self.mock_service = MagicMock()
        self.mock_get_service.return_value = self.mock_service

    def tearDown(self):
        self.get_user_patcher.stop()
        self.require_admin_patcher.stop()
        self.get_service_patcher.stop()

    @patch("src.handlers.features.delete_feature_env.main.success_response")
    def test_delete_feature_env_success(self, mock_success):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {
                "flag": "new_feature",
                "env": "dev",
            },
        }

        mock_success.return_value = {
            "statusCode": 200,
            "body": json.dumps({"message": "Environment removed"})
        }

        response = delete_feature_env_handler(event, context={})

        self.mock_get_user.assert_called_once_with(event)
        self.mock_require_admin.assert_called_once_with({"role": "ADMIN"})
        self.mock_service.remove_env.assert_called_once_with(
            "new_feature", "dev", actor="ADMIN"
        )
        mock_success.assert_called_once_with(
            {"message": "Environment removed"}, 200
        )

        self.assertEqual(response["statusCode"], 200)

    def test_delete_feature_env_unauthorized(self):
        self.mock_get_user.side_effect = AppException("Unauthorized", 401)

        event = {
            "pathParameters": {
                "flag": "new_feature",
                "env": "dev",
            }
        }

        response = delete_feature_env_handler(event, context={})

        self.assertEqual(response["statusCode"], 401)

    def test_delete_feature_env_not_admin(self):
        self.mock_get_user.return_value = {"role": "USER"}
        self.mock_require_admin.side_effect = AppException(
            "Admin access required", 403
        )

        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {
                "flag": "new_feature",
                "env": "dev",
            },
        }

        response = delete_feature_env_handler(event, context={})

        self.assertEqual(response["statusCode"], 403)

    def test_delete_feature_env_missing_flag(self):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {
                "env": "dev"
            },
        }

        response = delete_feature_env_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)

    def test_delete_feature_env_missing_env(self):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {
                "flag": "new_feature"
            },
        }

        response = delete_feature_env_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)

    def test_delete_feature_env_service_exception(self):
        self.mock_service.remove_env.side_effect = Exception("boom")

        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {
                "flag": "new_feature",
                "env": "dev",
            },
        }

        response = delete_feature_env_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)
