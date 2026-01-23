import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.features.delete_feature.main import delete_feature_handler
from error_handling.exceptions import AppException


class TestDeleteFeatureHandler(unittest.TestCase):

    @patch("src.handlers.features.delete_feature.main.get_current_user")
    @patch("src.handlers.features.delete_feature.main.require_admin")
    @patch("src.handlers.features.delete_feature.main.get_feature_service")
    @patch("src.handlers.features.delete_feature.main.success_response")
    def test_delete_feature_success(
        self,
        mock_success,
        mock_get_service,
        mock_require_admin,
        mock_get_user,
    ):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {"flag": "new_feature"},
        }

        mock_get_user.return_value = {"role": "ADMIN"}
        mock_require_admin.return_value = None

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_success.return_value = {
            "statusCode": 200,
            "body": json.dumps({"message": "Feature deleted"})
        }

        response = delete_feature_handler(event, context={})

        mock_get_user.assert_called_once_with(event)
        mock_require_admin.assert_called_once_with({"role": "ADMIN"})
        mock_service.delete_feature.assert_called_once_with(
            "new_feature", actor="ADMIN"
        )
        mock_success.assert_called_once_with(
            data={"message": "Feature deleted"},
            status_code=200,
        )

        self.assertEqual(response["statusCode"], 200)

    @patch("src.handlers.features.delete_feature.main.get_current_user")
    def test_delete_feature_unauthorized(self, mock_get_user):
        mock_get_user.side_effect = AppException("Unauthorized", 401)

        event = {
            "pathParameters": {"flag": "new_feature"}
        }

        response = delete_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 401)

    @patch("src.handlers.features.delete_feature.main.get_current_user")
    @patch("src.handlers.features.delete_feature.main.require_admin")
    def test_delete_feature_not_admin(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "USER"}
        mock_require_admin.side_effect = AppException(
            "Admin access required", 403
        )

        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {"flag": "new_feature"},
        }

        response = delete_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 403)

    @patch("src.handlers.features.delete_feature.main.get_current_user")
    @patch("src.handlers.features.delete_feature.main.require_admin")
    def test_delete_feature_missing_flag(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "ADMIN"}
        mock_require_admin.return_value = None

        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {}   # 👈 missing flag
        }

        response = delete_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)

    @patch("src.handlers.features.delete_feature.main.get_current_user")
    @patch("src.handlers.features.delete_feature.main.require_admin")
    @patch("src.handlers.features.delete_feature.main.get_feature_service")
    def test_delete_feature_service_exception(
        self, mock_get_service, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "ADMIN"}
        mock_require_admin.return_value = None

        mock_service = MagicMock()
        mock_service.delete_feature.side_effect = Exception("boom")
        mock_get_service.return_value = mock_service

        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {"flag": "new_feature"},
        }

        response = delete_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)
