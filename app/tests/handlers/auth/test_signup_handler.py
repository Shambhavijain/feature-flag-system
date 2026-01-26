import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.auth.signup_handler.main import handler
from dto.auth_dto import SignuprequestDTO


class TestSignupHandler(unittest.TestCase):

    def setUp(self):
        self.get_service_patcher = patch(
            "src.handlers.auth.signup_handler.main.get_auth_service"
        )
        self.mock_get_service = self.get_service_patcher.start()

        self.mock_service = MagicMock()
        self.mock_get_service.return_value = self.mock_service

    def tearDown(self):
        self.get_service_patcher.stop()

    @patch("src.handlers.auth.signup_handler.main.success_response")
    def test_signup_success(self, mock_success):
        event = {
            "body": json.dumps({
                "username": "test",
                "email": "test@example.com",
                "password": "Secret123!"
            })
        }

        self.mock_service.signup.return_value = {"message": "created"}

        mock_success.return_value = {
            "statusCode": 201,
            "body": json.dumps({"message": "created"})
        }

        response = handler(event, context={})

        self.mock_get_service.assert_called_once()
        self.mock_service.signup.assert_called_once()

        signup_arg = self.mock_service.signup.call_args[0][0]
        self.assertIsInstance(signup_arg, SignuprequestDTO)

        mock_success.assert_called_once_with({"message": "created"}, 201)
        self.assertEqual(response["statusCode"], 201)

    def test_signup_missing_field(self):
        event = {
            "body": json.dumps({
                "email": "test@example.com"
            })
        }

        response = handler(event, context={})

        self.assertEqual(response["statusCode"], 400)
        self.mock_service.signup.assert_not_called()
