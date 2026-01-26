import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.features.create_feature.main import create_feature_handler
from error_handling.exceptions import AppException


class TestCreateFeatureHandler(unittest.TestCase):

    def setUp(self):
        # Patch common dependencies
        self.get_user_patcher = patch(
            "src.handlers.features.create_feature.main.get_current_user"
        )
        self.require_admin_patcher = patch(
            "src.handlers.features.create_feature.main.require_admin"
        )
        self.get_service_patcher = patch(
            "src.handlers.features.create_feature.main.get_feature_service"
        )

        self.mock_get_user = self.get_user_patcher.start()
        self.mock_require_admin = self.require_admin_patcher.start()
        self.mock_get_service = self.get_service_patcher.start()

        # Common defaults
        self.mock_get_user.return_value = {"role": "ADMIN"}
        self.mock_require_admin.return_value = None

        self.mock_service = MagicMock()
        self.mock_get_service.return_value = self.mock_service

    def tearDown(self):
        self.get_user_patcher.stop()
        self.require_admin_patcher.stop()
        self.get_service_patcher.stop()

    @patch("src.handlers.features.create_feature.main.success_response")
    def test_create_feature_success(self, mock_success):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "body": json.dumps({
                "name": "NewFeature",
                "description": "test",
                "environments": {"dev": True}
            })
        }

        mock_success.return_value = {
            "statusCode": 201,
            "body": json.dumps({"message": "Feature Created"})
        }

        response = create_feature_handler(event, context={})

        self.mock_get_user.assert_called_once_with(event)
        self.mock_require_admin.assert_called_once_with({"role": "ADMIN"})
        self.mock_service.create_feature.assert_called_once()
        mock_success.assert_called_once_with(
            {"message": "Feature Created"}, 201
        )

        self.assertEqual(response["statusCode"], 201)

    def test_create_feature_missing_auth(self):
        self.mock_get_user.side_effect = AppException("Unauthorized", 401)

        event = {
            "body": json.dumps({
                "name": "NewFeature",
                "description": "test",
                "environments": {"dev": True}
            })
        }

        response = create_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 401)

    def test_create_feature_not_admin(self):
        self.mock_get_user.return_value = {"role": "USER"}
        self.mock_require_admin.side_effect = AppException(
            "Admin access required", 403
        )

        event = {
            "headers": {"Authorization": "Bearer token"},
            "body": json.dumps({
                "name": "NewFeature",
                "description": "test",
                "environments": {"dev": True}
            })
        }

        response = create_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 403)

    def test_create_feature_invalid_json(self):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "body": "{invalid-json"
        }

        response = create_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 400)

    def test_create_feature_missing_fields(self):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "body": json.dumps({
                "name": "NewFeature"
            })
        }

        response = create_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 400)

    def test_create_feature_service_exception(self):
        self.mock_service.create_feature.side_effect = Exception("boom")

        event = {
            "headers": {"Authorization": "Bearer token"},
            "body": json.dumps({
                "name": "NewFeature",
                "description": "test",
                "environments": {"dev": True}
            })
        }

        response = create_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)
