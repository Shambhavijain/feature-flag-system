import bcrypt
from dotenv import load_dotenv
from typing import Dict, Any
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from infra.config import get_env
from error_handling.exceptions import UnauthorizedException
from models.feature_model import FeatureEnv


load_dotenv()

JWT_SECRET_KEY = get_env("JWT_SECRET_KEY")
JWT_ALGORITHM = get_env("JWT_ALGORITHM", "HS256")

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not set")

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:

    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed.encode("utf-8"),
    )


def generate_jwt(payload: Dict[str, Any]) -> str:
    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def verify_jwt(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
    except ExpiredSignatureError:
        raise UnauthorizedException("Token expired")
    except JWTError:
        raise UnauthorizedException("Invalid token")


def map_env_for_audit(env: FeatureEnv) -> dict:
    return {
        "environment": env.environment.value,
        "enabled": env.enabled,
        "rollout_end_at": env.rollout_end_at,
        "updated_at": env.updated_at,
    }

def map_audit_items(items: list[dict]) -> list[dict]:
    return [
        {
            "action": item["action"],
            "actor": item["actor"],
            "old": item.get("old_value"),
            "new": item.get("new_value"),
            "timestamp": item["SK"].replace("LOGS#", ""),
        }
        for item in items
    ]

