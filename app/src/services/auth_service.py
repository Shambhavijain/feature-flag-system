import uuid
from datetime import datetime, timezone, timedelta

from repository.user_repository import UserRepository
from dto.auth_dto import SignuprequestDTO, LoginRequestDTO
from utils.utils import hash_password, verify_password
from constants.enums import Role
from error_handling.exceptions import ConflictException, UnauthorizedException
from models.user_model import UserModel
from utils.utils import generate_jwt

class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def signup(self, signup_request: SignuprequestDTO):
        email = signup_request.email.lower()
        existing_user = self.repo.get_user_by_email(email)
        if existing_user:
            raise ConflictException("User already exists")

        current_time = datetime.now(timezone.utc).isoformat()

        user = UserModel(
            username = signup_request.username,
            email = email,
            password_hash = hash_password(signup_request.password),
            role = Role.CLIENT,
            created_at = current_time
        )

        self.repo.create_user(user)
        return {"message": "User Created Successfully"}

    def login(self, login_request: LoginRequestDTO):
        user = self.repo.get_user_by_email(login_request.email.lower())

        if not user:
            raise UnauthorizedException("Invalid credentials")

        if not verify_password(login_request.password, user.password_hash):
            raise UnauthorizedException("Invalid credentials")

        token = generate_jwt({
            "email": user.email,
            "role": user.role.value,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        })

        return {"access_token": token}
