import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.features.list_features.main import list_features_handler
from error_handling.exceptions import AppException


class TestListFeaturesHandler(unittest.TestCase):

    def setUp(self):
        self.admin_user = {"role": "ADMIN"}
        self.normal_user = {"role": "USER"}

        self.valid_event = {
            "headers": {"Authorization": "Bearer token"},
        }

        self.get_service_patcher = patch(
            "src.handlers.features.list_features.main.get_feature_service"
        )
        self.mock_get_service = self.get_service_patcher.start()

        self.mock_service = MagicMock()
        self.mock_get_service.return_value = self.mock_service

    def tearDown(self):
        self.get_service_patcher.stop()

    @patch("src.handlers.features.list_features.main.get_current_user")
    @patch("src.handlers.features.list_features.main.require_admin")
    @patch("src.handlers.features.list_features.main.success_response")
    def test_list_features_success(
        self,
        mock_success,
        mock_require_admin,
        mock_get_user,
    ):
        mock_get_user.return_value = self.admin_user
        mock_require_admin.return_value = None

        feature1 = MagicMock()
        feature1.model_dump.return_value = {"name": "f1"}

        feature2 = MagicMock()
        feature2.model_dump.return_value = {"name": "f2"}

        self.mock_service.list_features.return_value = [
            feature1,
            feature2,
        ]

        mock_success.return_value = {
            "statusCode": 200,
            "body": json.dumps(
                [{"name": "f1"}, {"name": "f2"}]
            )
        }

        response = list_features_handler(self.valid_event, context={})

        self.mock_service.list_features.assert_called_once()
        mock_success.assert_called_once_with(
            [{"name": "f1"}, {"name": "f2"}]
        )
        self.assertEqual(response["statusCode"], 200)

    @patch("src.handlers.features.list_features.main.get_current_user")
    def test_list_features_unauthorized(self, mock_get_user):
        mock_get_user.side_effect = AppException("Unauthorized", 401)

        response = list_features_handler(self.valid_event, {})

        self.assertEqual(response["statusCode"], 401)


    @patch("src.handlers.features.list_features.main.get_current_user")
    @patch("src.handlers.features.list_features.main.require_admin")
    def test_list_features_not_admin(self, mock_require_admin, mock_get_user):
        mock_get_user.return_value = self.normal_user
        mock_require_admin.side_effect = AppException(
            "Admin access required", 403
        )

        response = list_features_handler(self.valid_event, {})

        self.assertEqual(response["statusCode"], 403)


    @patch("src.handlers.features.list_features.main.get_current_user")
    @patch("src.handlers.features.list_features.main.require_admin")
    def test_list_features_empty(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = self.admin_user
        mock_require_admin.return_value = None

        self.mock_service.list_features.return_value = []

        response = list_features_handler(self.valid_event, context={})

        self.assertEqual(response["statusCode"], 200)
        self.mock_service.list_features.assert_called_once()

    @patch("src.handlers.features.list_features.main.get_current_user")
    @patch("src.handlers.features.list_features.main.require_admin")
    def test_list_features_service_exception(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = self.admin_user
        mock_require_admin.return_value = None

        self.mock_service.list_features.side_effect = Exception("boom")

        response = list_features_handler(self.valid_event, context={})

        self.assertEqual(response["statusCode"], 500)
