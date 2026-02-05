import pytest
from jose import jwt

from src.utils.utils import (
    generate_jwt, 
    verify_jwt, 
    JWT_SECRET_KEY, 
    JWT_ALGORITHM,
    hash_password,
    verify_password,
    map_env_for_audit,
    map_audit_items,

    
)
from error_handling.exceptions import UnauthorizedException

def test_hash_and_verify_password_success():
    password = "Strong123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True


def test_verify_password_failure():
    password = "Strong123!"
    hashed = hash_password(password)

    assert verify_password("WrongPass", hashed) is False

def test_generate_and_verify_jwt():
    payload = {"user_id": "1", "role": "ADMIN"}
    token = generate_jwt(payload)

    decoded = verify_jwt(token)

    assert decoded["user_id"] == "1"
    assert decoded["role"] == "ADMIN"

def test_verify_jwt_expired():
    expired_token = jwt.encode(
        {"sub": "1", "exp": 0},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(UnauthorizedException, match="Token expired"):
        verify_jwt(expired_token)

def test_verify_jwt_invalid():
    with pytest.raises(UnauthorizedException, match="Invalid token"):
        verify_jwt("invalid.token.value")

def test_map_env_for_audit_success():
    item = {
        "environment": "dev",
        "enabled": True,
        "rollout_end_at": None,
        "updated_at": "2026-01-01T00:00:00Z"
    }

    result = map_env_for_audit(item)

    assert result == {
        "environment": "dev",
        "enabled": True,
        "rollout_end_at": None,
        "updated_at": "2026-01-01T00:00:00Z"
    }


def test_map_env_for_audit_none():
    assert map_env_for_audit(None) is None
from src.utils.utils import map_audit_items

def test_map_audit_items_success():
    items = [
        {
            "PK": "AUDIT#newfeature",
            "SK": "LOGS#2026-01-01T10:00:00Z",
            "action": "CREATE",
            "actor": "ADMIN",
            "old_value": None,
            "new_value": {"enabled": True},
        }
    ]

    result = map_audit_items(items)

    assert result == [
        {
            "action": "CREATE",
            "actor": "ADMIN",
            "old": None,
            "new": {"enabled": True},
            "timestamp": "2026-01-01T10:00:00Z",
        }
    ]

def test_map_audit_items_empty():
    assert map_audit_items([]) == []


