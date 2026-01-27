from dependency import get_current_user, require_admin, get_feature_service
from error_handling.responses import success_response
from utils.handler_decorator import error_handler


@error_handler
def delete_feature_env_handler(event, context):
    user = get_current_user(event)
    require_admin(user)

    path = event["pathParameters"]
    flag = path["flag"]
    env = path["env"]

    service = get_feature_service()
    service.remove_env(flag, env, actor="ADMIN")

    return success_response({"message": "Environment removed"}, 200)
