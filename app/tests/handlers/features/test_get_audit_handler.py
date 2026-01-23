import unittest
from unittest.mock import patch, MagicMock

from src.handlers.features.audit.get_audit.main import get_feature_audit_handler
from error_handling.exceptions import AppException


class TestGetFeatureAuditHandler(unittest.TestCase):

    @patch("src.handlers.features.audit.get_audit.main.get_current_user")
    @patch("src.handlers.features.audit.get_audit.main.require_admin")
    @patch("src.handlers.features.audit.get_audit.main.get_feature_service")
    @patch("src.handlers.features.audit.get_audit.main.success_response")
    def test_get_feature_audit_success(
        self,
        mock_success,
        mock_get_service,
        mock_require_admin,
        mock_get_user,
    ):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {"flag": "test-flag"},
        }

        mock_get_user.return_value = {"role": "ADMIN"}

        mock_service = MagicMock()
        mock_service.get_audit_logs.return_value = [
            {"action": "CREATE", "actor": "ADMIN"}
        ]
        mock_get_service.return_value = mock_service

        mock_success.return_value = {
            "statusCode": 200,
            "body": '{"data": []}'
        }

        response = get_feature_audit_handler(event, context={})

        mock_get_user.assert_called_once_with(event)
        mock_require_admin.assert_called_once_with({"role": "ADMIN"})
        mock_service.get_audit_logs.assert_called_once_with("test-flag")
        mock_success.assert_called_once()

        self.assertEqual(response["statusCode"], 200)

    @patch("src.handlers.features.audit.get_audit.main.get_current_user")
    def test_get_feature_audit_missing_auth(self, mock_get_user):
        mock_get_user.side_effect = AppException("Unauthorized", 401)

        event = {
            "pathParameters": {"flag": "test-flag"}
        }

        response = get_feature_audit_handler(event, context={})

        self.assertEqual(response["statusCode"], 401)

    @patch("src.handlers.features.audit.get_audit.main.get_current_user")
    @patch("src.handlers.features.audit.get_audit.main.require_admin")
    def test_get_feature_audit_not_admin(
        self, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "USER"}
        mock_require_admin.side_effect = AppException(
            "Admin access required", 403
        )

        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {"flag": "test-flag"},
        }

        response = get_feature_audit_handler(event, context={})

        self.assertEqual(response["statusCode"], 403)

    def test_get_feature_audit_missing_flag(self):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {}
        }

        response = get_feature_audit_handler(event, context={})

        # KeyError → wrapper → 500
        self.assertEqual(response["statusCode"], 500)

    @patch("src.handlers.features.audit.get_audit.main.get_current_user")
    @patch("src.handlers.features.audit.get_audit.main.require_admin")
    @patch("src.handlers.features.audit.get_audit.main.get_feature_service")
    def test_get_feature_audit_service_exception(
        self, mock_get_service, mock_require_admin, mock_get_user
    ):
        mock_get_user.return_value = {"role": "ADMIN"}
        mock_require_admin.return_value = None

        mock_service = MagicMock()
        mock_service.get_audit_logs.side_effect = Exception("boom")
        mock_get_service.return_value = mock_service

        event = {
            "headers": {"Authorization": "Bearer token"},
            "pathParameters": {"flag": "test-flag"},
        }

        response = get_feature_audit_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)
