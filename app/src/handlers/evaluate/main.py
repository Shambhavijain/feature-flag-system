import json

from dependency import get_current_user, get_feature_service
from dto.feature_dto import EvaluateDTO
from error_handling.responses import success_response
from utils.handler_decorator import error_handler


@error_handler
def evaluate_feature_handler(event, context):
    get_current_user(event)

    body = json.loads(event.get("body"))
    dto = EvaluateDTO(**body)

    service = get_feature_service()
    enabled = service.evaluate(dto)

    return success_response({"enabled": enabled}, 200)
