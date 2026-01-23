from datetime import datetime, timezone, timedelta

from repository.user_repository import UserRepository
from dto.auth_dto import SignuprequestDTO, LoginRequestDTO
from utils.utils import hash_password, verify_password, generate_jwt
from constants.enums import Role
from error_handling.exceptions import ConflictException, UnauthorizedException
from models.user_model import UserModel


class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def signup(self, signup_request: SignuprequestDTO):
        email = signup_request.email.lower()

        if self.repo.get_user_by_email(email):
            raise ConflictException("User already exists")

        user = UserModel(
            username=signup_request.username,
            email=email,
            password_hash=hash_password(signup_request.password),
            role=Role.CLIENT,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self.repo.create_user(user)

        return {"message": "User created successfully"}

    def login(self, login_request: LoginRequestDTO):
        user = self.repo.get_user_by_email(
            login_request.email.lower()
        )

        if not user or not verify_password(
            login_request.password,
            user.password_hash,
        ):
            raise UnauthorizedException("Invalid credentials")

        token = generate_jwt(
            {
                "email": user.email,
                "role": user.role.value,
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            }
        )

        return {"access_token": token}
