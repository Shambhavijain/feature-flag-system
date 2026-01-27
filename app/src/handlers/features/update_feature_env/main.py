import json
from dependency import get_current_user, require_admin, get_feature_service
from dto.feature_dto import UpdateFeatureEnvDTO
from error_handling.responses import success_response
from utils.handler_decorator import error_handler


@error_handler
def update_feature_env_handler(event, context):
    user = get_current_user(event)
    require_admin(user)

    path = event["pathParameters"]
    flag = path["flag"]
    env = path["env"]

    body = json.loads(event.get("body"))
    request = UpdateFeatureEnvDTO(**body)

    service = get_feature_service()
    service.update_env(flag, env, request, actor="ADMIN")

    return success_response(
        data={"message": "Environment updated"},
        status_code=200,
    )
