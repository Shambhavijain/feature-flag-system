import json

from dependency import get_auth_service
from utils.password_validator import validate_password
from error_handling.responses import success_response, error_response
from error_handling.exceptions import AppException
from dto.auth_dto import LoginRequestDTO

def handler(event,context):
    try:
        body = json.loads(event["body"])
        login_request = LoginRequestDTO(**body)
        auth_service = get_auth_service()
        token = auth_service.login(login_request)
        return success_response(token, 200)
    except AppException as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Internal Server Error", 500)