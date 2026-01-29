from botocore.exceptions import ClientError

from models.user_model import UserModel
from enums.enums import Role
from error_handling.exceptions import ConflictException


class UserRepository:
    def __init__(self, table):
        self.table = table

    def create_user(self, user: UserModel):
        try:
            self.table.put_item(
                Item={
                    "PK": f"USER#{user.email.lower()}",
                    "SK": "PROFILE",
                    "username": user.username,
                    "email": user.email,
                    "password_hash": user.password_hash,
                    "role": user.role.value,
                    "created_at": user.created_at,
                },
                ConditionExpression="attribute_not_exists(PK)"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise ConflictException("User already exists")
            raise

    def get_user_by_email(self, email: str) -> UserModel | None:
        email = email.lower()

        response = self.table.get_item(
            Key={
                "PK": f"USER#{email}",
                "SK": "PROFILE",
            }
        )

        item = response.get("Item")
        if not item:
            return None

        return UserModel(
            username=item["username"],
            email=item["email"],
            password_hash=item["password_hash"],
            role=Role(item["role"]),
            created_at=item["created_at"],
        )
