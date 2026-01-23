from infra.dynamodb import table
from repository.user_repository import UserRepository
from repository.feature_repository import FeatureRepository
from services.auth_service import AuthService
from services.feature_service import FeatureService
from utils.utils import verify_jwt
from error_handling.exceptions import UnauthorizedException, AppException
from models.user_model import UserModel


def get_auth_service() -> AuthService:
    repo = UserRepository(table)
    return AuthService(repo)


def get_feature_service() -> FeatureService:
    repo = FeatureRepository(table)
    return FeatureService(repo)




def get_current_user(event):
    headers = event.get("headers") or {}
    auth_header = headers.get("Authorization") or headers.get("authorization")

    if not auth_header:
        raise AppException("Missing Authorization header", 401)

    if not auth_header.startswith("Bearer "):
        raise AppException("Invalid Authorization header format", 401)

    token = auth_header.replace("Bearer ", "").strip()
    payload = verify_jwt(token)
    return payload



def require_admin(user: dict):
    if user["role"] != "ADMIN":
        raise UnauthorizedException("Admin access required")
