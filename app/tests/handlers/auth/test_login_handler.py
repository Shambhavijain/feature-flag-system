import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.auth.login_handler.main import handler
from dto.auth_dto import LoginRequestDTO


class TestLoginHandler(unittest.TestCase):

    def setUp(self):
        self.get_service_patcher = patch(
            "src.handlers.auth.login_handler.main.get_auth_service"
        )
        self.mock_get_service = self.get_service_patcher.start()

        self.mock_service = MagicMock()
        self.mock_get_service.return_value = self.mock_service

    def tearDown(self):
        self.get_service_patcher.stop()

    @patch("src.handlers.auth.login_handler.main.success_response")
    def test_login_success(self, mock_success):
        event = {
            "body": json.dumps({
                "email": "test@example.com",
                "password": "secret123"
            })
        }

        self.mock_service.login.return_value = "jwt-token"

        mock_success.return_value = {
            "statusCode": 200,
            "body": json.dumps({"token": "jwt-token"})
        }

        response = handler(event, context={})

        self.mock_get_service.assert_called_once()
        self.mock_service.login.assert_called_once()

        login_arg = self.mock_service.login.call_args[0][0]
        self.assertIsInstance(login_arg, LoginRequestDTO)

        mock_success.assert_called_once_with("jwt-token", 200)
        self.assertEqual(response["statusCode"], 200)

    def test_login_invalid_json(self):
        event = {"body": "{invalid-json"}
        response = handler(event, context={})

        self.assertEqual(response["statusCode"], 400)
        self.mock_service.login.assert_not_called()

    def test_login_service_exception(self):
        event = {
            "body": json.dumps({
                "email": "test@example.com",
                "password": "wrong"
            })
        }

        self.mock_service.login.side_effect = Exception("boom")

        response = handler(event, context={})

        self.assertEqual(response["statusCode"], 500)
