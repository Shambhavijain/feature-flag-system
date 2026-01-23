import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.features.update_feature_env.main import (
    update_feature_env_handler
)
from error_handling.exceptions import AppException
from dto.feature_dto import UpdateFeatureEnvDTO


class TestUpdateFeatureEnvHandler(unittest.TestCase):

    @patch("src.handlers.features.update_feature_env.main.get_current_user")
    @patch("src.handlers.features.update_feature_env.main.require_admin")
    @patch("src.handlers.features.update_feature_env.main.get_feature_service")
    @patch("src.handlers.features.update_feature_env.main.success_response")
    def test_update_feature_env_success(
        self,
        mock_success,
        mock_get_service,
        mock_require_admin,
        mock_get_user,
    ):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {
                "flag": "new_feature",
                "env": "dev",
            },
            "body": json.dumps({
                "enabled": True,
                "rollout_end_at": None
            }),
        }

        mock_get_user.return_value = {"role": "ADMIN"}
        mock_require_admin.return_value = None

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_success.return_value = {
            "statusCode": 200,
            "body": json.dumps({"message": "Environment updated"})
        }

        response = update_feature_env_handler(event, context={})

        mock_get_user.assert_called_once_with(event)
        mock_require_admin.assert_called_once_with({"role": "ADMIN"})
        mock_service.update_env.assert_called_once()

        args = mock_service.update_env.call_args[0]
        self.assertEqual(args[0], "new_feature")
        self.assertEqual(args[1], "dev")
        self.assertIsInstance(args[2], UpdateFeatureEnvDTO)

        mock_success.assert_called_once_with(
            data={"message": "Environment updated"},
            status_code=200,
        )

        self.assertEqual(response["statusCode"], 200)

    @patch("src.handlers.features.update_feature_env.main.get_current_user")
    def test_update_feature_env_unauthorized(self, mock_get_user):
        mock_get_user.side_effect = AppException("Unauthorized", 401)

        event = {
            "pathParameters": {
                "flag": "new_feature",
                "env": "dev",
            },
            "body": json.dumps({"enabled": True}),
        }

        response = update_feature_env_handler(event, context={})

        self.assertEqual(response["statusCode"], 401)

    @patch("src.handlers.features.update_feature_env.main.get_current_user")
    @patch("src.handlers.features.update_feature_env.main.require_admin")
    def test_update_feature_env_not_admin(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "USER"}
        mock_require_admin.side_effect = AppException(
            "Admin access required", 403
        )

        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {
                "flag": "new_feature",
                "env": "dev",
            },
            "body": json.dumps({"enabled": True}),
        }

        response = update_feature_env_handler(event, context={})

        self.assertEqual(response["statusCode"], 403)

    def test_update_feature_env_invalid_json(self):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {
                "flag": "new_feature",
                "env": "dev",
            },
            "body": "{invalid-json",
        }

        response = update_feature_env_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)

    def test_update_feature_env_missing_fields(self):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {
                "flag": "new_feature",
                "env": "dev",
            },
            "body": json.dumps({}),
        }

        response = update_feature_env_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)

    @patch("src.handlers.features.update_feature_env.main.get_current_user")
    @patch("src.handlers.features.update_feature_env.main.require_admin")
    @patch("src.handlers.features.update_feature_env.main.get_feature_service")
    def test_update_feature_env_service_exception(
        self, mock_get_service, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "ADMIN"}
        mock_require_admin.return_value = None

        mock_service = MagicMock()
        mock_service.update_env.side_effect = Exception("boom")
        mock_get_service.return_value = mock_service

        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {
                "flag": "new_feature",
                "env": "dev",
            },
            "body": json.dumps({"enabled": True}),
        }

        response = update_feature_env_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)
