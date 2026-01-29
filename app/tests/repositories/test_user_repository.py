import unittest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError

from repository.user_repository import UserRepository
from models.user_model import UserModel
from enums.enums import Role
from error_handling.exceptions import ConflictException

class TestUserRepository(unittest.TestCase):

    def setUp(self):
        self.mock_table = MagicMock()
        self.repo = UserRepository(self.mock_table)

        self.user = UserModel(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role=Role.CLIENT,
            created_at="2024-01-01T00:00:00Z"
        )
        
    def test_create_user_success(self):
        self.mock_table.put_item.return_value = {}
        self.repo.create_user(self.user)
        self.mock_table.put_item.assert_called_once()

    def test_create_user_conflict(self):
        self.mock_table.put_item.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ConditionalCheckFailedException"}
            },
            operation_name="PutItem"
        )

        with self.assertRaises(ConflictException):
            self.repo.create_user(self.user)
    
    def test_get_user_by_email_found(self):
        self.mock_table.get_item.return_value = {
            "Item": {
                "username": "testuser",
                "email": "test@example.com",
                "password_hash": "hashed",
                "role": "CLIENT",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }

        user = self.repo.get_user_by_email("test@example.com")

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")

    def test_get_user_by_email_not_found(self):
        self.mock_table.get_item.return_value = {}

        user = self.repo.get_user_by_email("missing@example.com")

        self.assertIsNone(user)
        
    def test_create_user_unexpected_client_error(self):
        self.mock_table.put_item.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ProvisionedThroughputExceededException"}
            },
            operation_name="PutItem"
        )

        with self.assertRaises(ClientError):
            self.repo.create_user(self.user)
