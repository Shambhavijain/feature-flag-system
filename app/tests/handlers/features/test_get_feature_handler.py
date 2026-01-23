import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.features.get_feature.main import get_feature_handler
from error_handling.exceptions import AppException


class TestGetFeatureHandler(unittest.TestCase):

    @patch("src.handlers.features.get_feature.main.get_current_user")
    @patch("src.handlers.features.get_feature.main.require_admin")
    @patch("src.handlers.features.get_feature.main.get_feature_service")
    @patch("src.handlers.features.get_feature.main.success_response")
    def test_get_feature_success(
        self,
        mock_success,
        mock_get_service,
        mock_require_admin,
        mock_get_user,
    ):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {
                "flag": "new_feature"
            },
        }

        mock_get_user.return_value = {"role": "ADMIN"}
        mock_require_admin.return_value = None

        mock_service = MagicMock()
        mock_service.get_feature.return_value = {
            "name": "new_feature",
            "description": "test feature",
            "environments": {"dev": True},
        }
        mock_get_service.return_value = mock_service

        mock_success.return_value = {
            "statusCode": 200,
            "body": json.dumps({"data": mock_service.get_feature.return_value})
        }

        response = get_feature_handler(event, context={})

        mock_get_user.assert_called_once_with(event)
        mock_require_admin.assert_called_once_with({"role": "ADMIN"})
        mock_service.get_feature.assert_called_once_with("new_feature")
        mock_success.assert_called_once_with(
            data=mock_service.get_feature.return_value,
            status_code=200
        )

        self.assertEqual(response["statusCode"], 200)

    @patch("src.handlers.features.get_feature.main.get_current_user")
    def test_get_feature_unauthorized(self, mock_get_user):
        mock_get_user.side_effect = AppException("Unauthorized", 401)

        event = {
            "pathParameters": {
                "flag": "new_feature"
            }
        }

        response = get_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 401)

    @patch("src.handlers.features.get_feature.main.get_current_user")
    @patch("src.handlers.features.get_feature.main.require_admin")
    def test_get_feature_not_admin(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "USER"}
        mock_require_admin.side_effect = AppException(
            "Admin access required", 403
        )

        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {
                "flag": "new_feature"
            },
        }

        response = get_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 403)

    @patch("src.handlers.features.get_feature.main.get_current_user")
    @patch("src.handlers.features.get_feature.main.require_admin")
    def test_get_feature_missing_flag(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "ADMIN"}
        mock_require_admin.return_value = None

        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {}
        }

        response = get_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)

    @patch("src.handlers.features.get_feature.main.get_current_user")
    @patch("src.handlers.features.get_feature.main.require_admin")
    @patch("src.handlers.features.get_feature.main.get_feature_service")
    def test_get_feature_service_exception(
        self, mock_get_service, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "ADMIN"}
        mock_require_admin.return_value = None

        mock_service = MagicMock()
        mock_service.get_feature.side_effect = Exception("boom")
        mock_get_service.return_value = mock_service

        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {
                "flag": "new_feature"
            },
        }

        response = get_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)
