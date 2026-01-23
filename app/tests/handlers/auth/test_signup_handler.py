import json
import unittest
from unittest.mock import patch, MagicMock

from src.handlers.auth.signup_handler.main import handler
from dto.auth_dto import SignuprequestDTO

class TestSignupHandler(unittest.TestCase):

    @patch("src.handlers.auth.signup_handler.main.get_auth_service")
    @patch("src.handlers.auth.signup_handler.main.success_response")
    def test_signup_success(self, mock_success, mock_get_service):
        event = {
            "body": json.dumps({
                "username": "test",
                "email": "test@example.com",
                "password": "Secret123!"
            })
        }

        mock_service = MagicMock()
        mock_service.signup.return_value = {"message": "created"}
        mock_get_service.return_value = mock_service

        mock_success.return_value = {
            "statusCode": 201,
            "body": json.dumps({"message": "created"})
        }

        response = handler(event, context={})

        mock_service.signup.assert_called_once()
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
