from dataclasses import dataclass
from constants.enums import Role


@dataclass
class UserModel:
    username: str
    email: str
    password_hash: str
    role: Role
    created_at: str
   
