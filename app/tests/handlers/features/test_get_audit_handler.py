import unittest
from unittest.mock import patch, MagicMock

from src.handlers.features.audit.get_audit.main import get_feature_audit_handler
from error_handling.exceptions import AppException


class TestGetFeatureAuditHandler(unittest.TestCase):

    def setUp(self):
        self.admin_user = {"role": "ADMIN"}
        self.normal_user = {"role": "USER"}

        self.valid_event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {"flag": "test-flag"},
        }

        self.get_service_patcher = patch(
            "src.handlers.features.audit.get_audit.main.get_feature_service"
        )
        self.mock_get_service = self.get_service_patcher.start()

        self.mock_service = MagicMock()
        self.mock_get_service.return_value = self.mock_service

    def tearDown(self):
        self.get_service_patcher.stop()

    @patch("src.handlers.features.audit.get_audit.main.get_current_user")
    @patch("src.handlers.features.audit.get_audit.main.require_admin")
    @patch("src.handlers.features.audit.get_audit.main.success_response")
    def test_get_feature_audit_success(
        self,
        mock_success,
        mock_require_admin,
        mock_get_user,
    ):
        mock_get_user.return_value = self.admin_user
        mock_require_admin.return_value = None

        self.mock_service.get_audit_logs.return_value = [
            {"action": "CREATE", "actor": "ADMIN"}
        ]

        mock_success.return_value = {
            "statusCode": 200,
            "body": '{"data": []}'
        }

        response = get_feature_audit_handler(self.valid_event, context={})

        mock_get_user.assert_called_once_with(self.valid_event)
        mock_require_admin.assert_called_once_with(self.admin_user)
        self.mock_service.get_audit_logs.assert_called_once_with("test-flag")

        mock_success.assert_called_once()
        self.assertEqual(response["statusCode"], 200)

    @patch("src.handlers.features.audit.get_audit.main.get_current_user")
    def test_get_feature_audit_missing_auth(self, mock_get_user):
        mock_get_user.side_effect = AppException("Unauthorized", 401)

        response = get_feature_audit_handler(self.valid_event, context={})

        self.assertEqual(response["statusCode"], 401)
        self.mock_service.get_audit_logs.assert_not_called()

    @patch("src.handlers.features.audit.get_audit.main.get_current_user")
    @patch("src.handlers.features.audit.get_audit.main.require_admin")
    def test_get_feature_audit_not_admin(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = self.normal_user
        mock_require_admin.side_effect = AppException(
            "Admin access required", 403
        )

        response = get_feature_audit_handler(self.valid_event, context={})

        self.assertEqual(response["statusCode"], 403)
        self.mock_service.get_audit_logs.assert_not_called()

    def test_get_feature_audit_missing_flag(self):
        event = {
            **self.valid_event,
            "pathParameters": {},
        }

        response = get_feature_audit_handler(event, context={})

        self.assertEqual(response["statusCode"], 401)
        self.mock_service.get_audit_logs.assert_not_called()

    @patch("src.handlers.features.audit.get_audit.main.get_current_user")
    @patch("src.handlers.features.audit.get_audit.main.require_admin")
    def test_get_feature_audit_service_exception(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = self.admin_user
        mock_require_admin.return_value = None

        self.mock_service.get_audit_logs.side_effect = Exception("boom")

        response = get_feature_audit_handler(self.valid_event, context={})

        self.assertEqual(response["statusCode"], 500)
