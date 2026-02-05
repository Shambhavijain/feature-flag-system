import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.features.update_feature_env.main import (
    update_feature_env_handler
)
from error_handling.exceptions import AppException
from dto.feature_dto import UpdateFeatureEnvDTO


class TestUpdateFeatureEnvHandler(unittest.TestCase):

    def setUp(self):
        self.admin_user = {"role": "ADMIN"}
        self.normal_user = {"role": "USER"}

        self.valid_event = {
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

        self.get_service_patcher = patch(
            "src.handlers.features.update_feature_env.main.get_feature_service"
        )
        self.mock_get_service = self.get_service_patcher.start()

        self.mock_service = MagicMock()
        self.mock_get_service.return_value = self.mock_service

    def tearDown(self):
        self.get_service_patcher.stop()

    @patch("src.handlers.features.update_feature_env.main.get_current_user")
    @patch("src.handlers.features.update_feature_env.main.require_admin")
    @patch("src.handlers.features.update_feature_env.main.success_response")
    def test_update_feature_env_success(
        self,
        mock_success,
        mock_require_admin,
        mock_get_user,
    ):
        mock_get_user.return_value = self.admin_user
        mock_require_admin.return_value = None

        mock_success.return_value = {
            "statusCode": 200,
            "body": json.dumps({"message": "Environment updated"})
        }

        response = update_feature_env_handler(self.valid_event, context={})

        self.mock_service.update_env.assert_called_once()

        args = self.mock_service.update_env.call_args[0]
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

        response = update_feature_env_handler(self.valid_event, context={})

        self.assertEqual(response["statusCode"], 401)
        self.mock_service.update_env.assert_not_called()

    @patch("src.handlers.features.update_feature_env.main.get_current_user")
    @patch("src.handlers.features.update_feature_env.main.require_admin")
    def test_update_feature_env_not_admin(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = self.normal_user
        mock_require_admin.side_effect = AppException(
            "Admin access required", 403
        )

        response = update_feature_env_handler(self.valid_event, context={})

        self.assertEqual(response["statusCode"], 403)
        self.mock_service.update_env.assert_not_called()

    def test_update_feature_env_invalid_json(self):
        event = {
            **self.valid_event,
            "body": "{invalid-json",
        }

        response = update_feature_env_handler(event, context={})

        self.assertEqual(response["statusCode"], 401)
        self.mock_service.update_env.assert_not_called()

    def test_update_feature_env_missing_fields(self):
        event = {
            **self.valid_event,
            "body": json.dumps({}),
        }

        response = update_feature_env_handler(event, context={})

        self.assertEqual(response["statusCode"], 401)
        self.mock_service.update_env.assert_not_called()

    @patch("src.handlers.features.update_feature_env.main.get_current_user")
    @patch("src.handlers.features.update_feature_env.main.require_admin")
    def test_update_feature_env_service_exception(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = self.admin_user
        mock_require_admin.return_value = None

        self.mock_service.update_env.side_effect = Exception("boom")

        response = update_feature_env_handler(self.valid_event, context={})

        self.assertEqual(response["statusCode"], 500)
