import pytest
from src.utils.password_validator import validate_password


def test_valid_password():
    assert validate_password("Strong123!") == "Strong123!"


def test_password_missing_lowercase():
    with pytest.raises(ValueError):
        validate_password("PASSWORD1")


def test_password_missing_digit():
    with pytest.raises(ValueError):
        validate_password("Password")
