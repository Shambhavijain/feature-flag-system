import json

from dto.auth_dto import SignuprequestDTO
from dependency import get_auth_service
from error_handling.exceptions import AppException
from error_handling.responses import success_response,error_response
from utils.handler_decorator import lambda_handler_wrapper


@lambda_handler_wrapper
def handler(event, context):
    
    body = json.loads(event["body"])
    signup_request = SignuprequestDTO(
        username = body.get("username"),
        email= body.get("email"),
        password = body.get("password")
    )
    auth_service = get_auth_service()
    result = auth_service.signup(signup_request)
    return success_response(result, 201)
    