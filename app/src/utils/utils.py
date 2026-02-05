import bcrypt
from dotenv import load_dotenv
from typing import Dict, Any
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from infra.config import get_env
from error_handling.exceptions import UnauthorizedException


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


def map_env_for_audit(item: dict | None) -> dict | None:
    if not item:
        return None

    return {
        "environment": item["environment"],
        "enabled": item["enabled"],
        "rollout_end_at": item.get("rollout_end_at"),
        "updated_at": item.get("updated_at"),
    }


def map_feature_items(
    feature_item: dict,
    env_items: list[dict]
) -> dict:
    feature = {
        "feature": feature_item["SK"].replace("FEATURE#", ""),
        "description": feature_item.get("description"),
        "created_at": feature_item.get("created_at"),
        "environments": {},
    }

    for env in env_items:
        env_name = env["SK"].replace("ENV#", "")
        feature["environments"][env_name] = {
            "enabled": env["enabled"],
            "rollout_end_at": env.get("rollout_end_at"),
            "updated_at": env.get("updated_at"),
        }

    return feature



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

