import pytest
from unittest.mock import patch

from error_handling.exceptions import AppException, UnauthorizedException
from src.dependency import  get_current_user,get_auth_service, get_feature_service
from services.auth_service import AuthService
from services.feature_service import FeatureService


def test_get_auth_service():
    service = get_auth_service()
    assert isinstance(service, AuthService)


def test_get_feature_service():
    service = get_feature_service()
    assert isinstance(service, FeatureService)



def test_get_current_user_missing_header():
    event = {"headers": {}}

    with pytest.raises(AppException) as exc:
        get_current_user(event)

    assert exc.value.status_code == 401

def test_get_current_user_invalid_header_format():
    event = {
        "headers": {"Authorization": "Token abc123"}
    }

    with pytest.raises(AppException) as exc:
        get_current_user(event)

    assert exc.value.status_code == 401



@patch("src.dependency.verify_jwt")
def test_get_current_user_success(mock_verify):
    mock_verify.return_value = {"user_id": "1", "role": "ADMIN"}

    event = {
        "headers": {"Authorization": "Bearer valid.jwt.token"}
    }

    user = get_current_user(event)

    mock_verify.assert_called_once_with("valid.jwt.token")
    assert user["role"] == "ADMIN"

from src.dependency import require_admin


def test_require_admin_success():
    require_admin({"role": "ADMIN"})  # should not raise



def test_require_admin_unauthorized():
    with pytest.raises(UnauthorizedException):
        require_admin({"role": "USER"})
