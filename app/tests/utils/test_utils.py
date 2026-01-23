import pytest
from jose import jwt

from src.utils.utils import (
    generate_jwt, 
    verify_jwt, 
    JWT_SECRET_KEY, 
    JWT_ALGORITHM,
    hash_password,
    verify_password,
    
)


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

    with pytest.raises(ValueError, match="Token expired"):
        verify_jwt(expired_token)

def test_verify_jwt_invalid():
    with pytest.raises(ValueError, match="Invalid token"):
        verify_jwt("invalid.token.value")
