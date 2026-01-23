import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.features.create_feature.main import create_feature_handler
from error_handling.exceptions import AppException


class TestCreateFeatureHandler(unittest.TestCase):

    @patch("src.handlers.features.create_feature.main.get_current_user")
    @patch("src.handlers.features.create_feature.main.require_admin")
    @patch("src.handlers.features.create_feature.main.get_feature_service")
    @patch("src.handlers.features.create_feature.main.success_response")
    def test_create_feature_success(
        self,
        mock_success,
        mock_get_service,
        mock_require_admin,
        mock_get_user,
    ):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "body": json.dumps({
                "name": "NewFeature",
                "description": "test",
                "environments": {"dev": True}
            })
        }

        mock_get_user.return_value = {"role": "ADMIN"}

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_success.return_value = {
            "statusCode": 201,
            "body": json.dumps({"message": "Feature Created"})
        }

        response = create_feature_handler(event, context={})

        mock_get_user.assert_called_once_with(event)
        mock_require_admin.assert_called_once_with({"role": "ADMIN"})
        mock_service.create_feature.assert_called_once()
        mock_success.assert_called_once_with(
            {"message": "Feature Created"}, 201
        )

        self.assertEqual(response["statusCode"], 201)

    @patch("src.handlers.features.create_feature.main.get_current_user")
    def test_create_feature_missing_auth(self, mock_get_user):
        mock_get_user.side_effect = AppException("Unauthorized", 401)

        event = {
            "body": json.dumps({
                "name": "NewFeature",
                "description": "test",
                "environments": {"dev": True}
            })
        }

        response = create_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 401)

    @patch("src.handlers.features.create_feature.main.get_current_user")
    @patch("src.handlers.features.create_feature.main.require_admin")
    def test_create_feature_not_admin(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "USER"}
        mock_require_admin.side_effect = AppException(
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

    @patch("src.handlers.features.create_feature.main.get_current_user")
    @patch("src.handlers.features.create_feature.main.require_admin")
    def test_create_feature_invalid_json(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "ADMIN"}
        mock_require_admin.return_value = None

        event = {
            "headers": {"Authorization": "Bearer token"},
            "body": "{invalid-json"
        }

        response = create_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 400)


    @patch("src.handlers.features.create_feature.main.get_current_user")
    @patch("src.handlers.features.create_feature.main.require_admin")
    def test_create_feature_missing_fields(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "ADMIN"}
        mock_require_admin.return_value = None

        event = {
            "headers": {"Authorization": "Bearer token"},
            "body": json.dumps({
                "name": "NewFeature"
            })
        }

        response = create_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 400)


    @patch("src.handlers.features.create_feature.main.get_current_user")
    @patch("src.handlers.features.create_feature.main.require_admin")
    @patch("src.handlers.features.create_feature.main.get_feature_service")
    def test_create_feature_service_exception(
        self, mock_get_service, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "ADMIN"}
        mock_require_admin.return_value = None

        mock_service = MagicMock()
        mock_service.create_feature.side_effect = Exception("boom")
        mock_get_service.return_value = mock_service

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
