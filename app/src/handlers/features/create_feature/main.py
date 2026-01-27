import json

from dependency import get_current_user, require_admin, get_feature_service
from dto.feature_dto import CreateFeatureDTO
from error_handling.responses import success_response
from utils.handler_decorator import error_handler


@error_handler
def create_feature_handler(event, context):
    user = get_current_user(event)
    require_admin(user)

    body = json.loads(event.get("body"))
    dto = CreateFeatureDTO(**body)

    service = get_feature_service()
    service.create_feature(dto, actor="ADMIN")

    return success_response({"message": "Feature Created"}, 201)
