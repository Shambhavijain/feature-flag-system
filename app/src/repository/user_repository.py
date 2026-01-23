import boto3

from models.user_model import UserModel
from constants.enums import Role


class UserRepository:
    def __init__(self, table:str):
        self.table = table

    def create_user(self, user:UserModel):
       self.table.put_item(
        Item = {
            "PK": f"USER#{user.email.lower()}",
            "SK": "PROFILE",
            "username":user.username,
            "email":user.email,
            "password_hash":user.password_hash,
            "role":user.role.value,
            "created_at":user.created_at,
        },
        ConditionExpression="attribute_not_exists(SK)"
       )

    def get_user_by_email(self, email:str)->UserModel|None:
        email = email.lower()
        user = self.table.get_item(
            Key={
                "PK": f"USER#{email.lower()}",
                "SK": "PROFILE",
            }
        )

        item = user.get("Item")
        if not item:
            return None

        return UserModel(
            username=item["username"],
            email=item["email"],
            password_hash=item["password_hash"],
            role=Role(item["role"]),
            created_at=item["created_at"],
        )
        