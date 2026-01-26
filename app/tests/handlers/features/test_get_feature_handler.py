import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.features.get_feature.main import get_feature_handler
from error_handling.exceptions import AppException


class TestGetFeatureHandler(unittest.TestCase):

    def setUp(self):
        self.admin_user = {"role": "ADMIN"}
        self.normal_user = {"role": "USER"}

        self.valid_event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {"flag": "new_feature"},
        }

        self.get_service_patcher = patch(
            "src.handlers.features.get_feature.main.get_feature_service"
        )
        self.mock_get_service = self.get_service_patcher.start()

        self.mock_service = MagicMock()
        self.mock_get_service.return_value = self.mock_service

    def tearDown(self):
        self.get_service_patcher.stop()

    @patch("src.handlers.features.get_feature.main.get_current_user")
    @patch("src.handlers.features.get_feature.main.require_admin")
    @patch("src.handlers.features.get_feature.main.success_response")
    def test_get_feature_success(
        self,
        mock_success,
        mock_require_admin,
        mock_get_user,
    ):
        mock_get_user.return_value = self.admin_user
        mock_require_admin.return_value = None

        feature_data = {
            "name": "new_feature",
            "description": "test feature",
            "environments": {"dev": True},
        }
        self.mock_service.get_feature.return_value = feature_data

        mock_success.return_value = {
            "statusCode": 200,
            "body": json.dumps({"data": feature_data})
        }

        response = get_feature_handler(self.valid_event, context={})

        self.mock_service.get_feature.assert_called_once_with("new_feature")
        mock_success.assert_called_once_with(
            data=feature_data,
            status_code=200
        )
        self.assertEqual(response["statusCode"], 200)

    @patch("src.handlers.features.get_feature.main.get_current_user")
    def test_get_feature_unauthorized(self, mock_get_user):
        mock_get_user.side_effect = AppException("Unauthorized", 401)

        response = get_feature_handler(self.valid_event, context={})

        self.assertEqual(response["statusCode"], 401)
        self.mock_service.get_feature.assert_not_called()

    @patch("src.handlers.features.get_feature.main.get_current_user")
    @patch("src.handlers.features.get_feature.main.require_admin")
    def test_get_feature_not_admin(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = self.normal_user
        mock_require_admin.side_effect = AppException(
            "Admin access required", 403
        )

        response = get_feature_handler(self.valid_event, context={})

        self.assertEqual(response["statusCode"], 403)
        self.mock_service.get_feature.assert_not_called()

    @patch("src.handlers.features.get_feature.main.get_current_user")
    @patch("src.handlers.features.get_feature.main.require_admin")
    def test_get_feature_missing_flag(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = self.admin_user
        mock_require_admin.return_value = None

        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {}
        }

        response = get_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)

    @patch("src.handlers.features.get_feature.main.get_current_user")
    @patch("src.handlers.features.get_feature.main.require_admin")
    def test_get_feature_service_exception(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = self.admin_user
        mock_require_admin.return_value = None

        self.mock_service.get_feature.side_effect = Exception("boom")

        response = get_feature_handler(self.valid_event, context={})

        self.assertEqual(response["statusCode"], 500)
