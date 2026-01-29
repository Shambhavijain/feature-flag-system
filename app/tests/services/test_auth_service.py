import unittest
from unittest.mock import MagicMock, patch

from services.auth_service import AuthService
from dto.auth_dto import SignuprequestDTO, LoginRequestDTO
from error_handling.exceptions import ConflictException, UnauthorizedException
from models.user_model import UserModel
from enums.enums import Role


class TestAuthService(unittest.TestCase):

    def setUp(self):
        self.repo = MagicMock()
        self.service = AuthService(self.repo)

    @patch("services.auth_service.hash_password")
    def test_signup_success(self, mock_hash):
        self.repo.get_user_by_email.return_value = None
        mock_hash.return_value = "hashed-password"

        req = SignuprequestDTO(
            username="test",
            email="test@example.com",
            password="password123"
        )

        result = self.service.signup(req)

        self.repo.create_user.assert_called_once()
        self.assertEqual(result["message"], "User created successfully")

    def test_signup_conflict(self):
        self.repo.get_user_by_email.return_value = MagicMock()

        req = SignuprequestDTO(
            username="test",
            email="test@example.com",
            password="password123"
        )

        with self.assertRaises(ConflictException):
            self.service.signup(req)

    @patch("services.auth_service.verify_password")
    @patch("services.auth_service.generate_jwt")
    def test_login_success(self, mock_jwt, mock_verify):
        mock_verify.return_value = True
        mock_jwt.return_value = "jwt-token"

        user = UserModel(
            username="test",
            email="test@example.com",
            password_hash="hashed",
            role=Role.CLIENT,
            created_at="now",
        )

        self.repo.get_user_by_email.return_value = user

        req = LoginRequestDTO(
            email="test@example.com",
            password="password123"
        )

        result = self.service.login(req)

        self.assertIn("access_token", result)
        self.assertEqual(result["access_token"], "jwt-token")

    @patch("services.auth_service.verify_password")
    def test_login_invalid_credentials(self, mock_verify):
        mock_verify.return_value = False
        self.repo.get_user_by_email.return_value = MagicMock()

        req = LoginRequestDTO(
            email="test@example.com",
            password="wrong"
        )

        with self.assertRaises(UnauthorizedException):
            self.service.login(req)
