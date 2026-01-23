import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.evaluate.main import evaluate_feature_handler
from dto.feature_dto import EvaluateDTO
from constants.enums import Environment
from error_handling.exceptions import AppException


class TestEvaluateFeatureHandler(unittest.TestCase):

    @patch("src.handlers.evaluate.main.get_current_user")
    @patch("src.handlers.evaluate.main.get_feature_service")
    @patch("src.handlers.evaluate.main.success_response")
    def test_evaluate_feature_enabled(
        self, mock_success, mock_get_service, mock_get_user
    ):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "body": json.dumps({
                "feature": "new-ui",
                "environment": Environment.DEV.value
            })
        }

        mock_get_user.return_value = {"user_id": "1"}

        mock_service = MagicMock()
        mock_service.evaluate.return_value = True
        mock_get_service.return_value = mock_service

        mock_success.return_value = {
            "statusCode": 200,
            "body": json.dumps({"enabled": True})
        }

        response = evaluate_feature_handler(event, context={})

        mock_get_user.assert_called_once_with(event)
        mock_service.evaluate.assert_called_once()
        mock_success.assert_called_once_with({"enabled": True}, 200)

        self.assertEqual(response["statusCode"], 200)

    @patch("src.handlers.evaluate.main.get_current_user")
    def test_evaluate_invalid_json(self, mock_get_user):
        event = {
            "headers": {"Authorization": "Bearer token"},
            "body": "{invalid-json"
        }

        response = evaluate_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 400)

    @patch("src.handlers.evaluate.main.get_current_user")
    def test_missing_authorization(self, mock_get_user):
        mock_get_user.side_effect = AppException("Unauthorized", 401)

        event = {
            "body": json.dumps({
                "feature": "new-ui",
                "environment": Environment.DEV.value
            })
        }

        response = evaluate_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 401)

    @patch("src.handlers.evaluate.main.get_current_user")
    @patch("src.handlers.evaluate.main.get_feature_service")
    def test_service_exception(self, mock_get_service, mock_get_user):
        mock_get_user.return_value = {"user_id": "1"}

        mock_service = MagicMock()
        mock_service.evaluate.side_effect = Exception("boom")
        mock_get_service.return_value = mock_service

        event = {
            "headers": {"Authorization": "Bearer token"},
            "body": json.dumps({
                "feature": "new-ui",
                "environment": Environment.DEV.value
            })
        }

        response = evaluate_feature_handler(event, context={})

        self.assertEqual(response["statusCode"], 500)
