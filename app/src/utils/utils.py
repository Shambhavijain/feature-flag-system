import bcrypt
from dotenv import load_dotenv
from typing import Dict, Any
from jose import jwt, JWTError, ExpiredSignatureError

from infra.env import get_env
from passlib.context import CryptContext


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
        raise ValueError("Token expired")
    except JWTError:
        raise ValueError("Invalid token")


def map_env_for_audit(item: dict | None) -> dict | None:
    if not item:
        return None

    return {
        "environment": item["environment"],
        "enabled": item["enabled"],
        "rollout_end_at": item.get("rollout_end_at"),
        "updated_at": item.get("updated_at"),
    }


def map_feature_items(items: list[dict]) -> dict:
    feature = {
        "feature": None,
        "description": None,
        "environments": {},
    }

    for item in items:
        sk = item["SK"]

        if sk == "META":
            feature["feature"] = item["PK"].replace("FEATURE#", "")
            feature["description"] = item.get("description")

        elif sk.startswith("ENV#"):
            env = sk.replace("ENV#", "")
            feature["environments"][env] = {
                "enabled": item["enabled"],
                "rollout_end_at": item.get("rollout_end_at"),
                "updated_at": item.get("updated_at"),
            }

    return feature

def map_audit_items(items: list[dict]) -> list[dict]:
    return [
        {
            "action": i["action"],
            "actor": i["actor"],
            "old": i.get("old_value"),
            "new": i.get("new_value"),
            "timestamp": i["created_at"],
        }
        for i in items
    ]
