import json
from dependency import get_current_user, require_admin, get_feature_service
from error_handling.responses import success_response, error_response
from error_handling.exceptions import AppException

def delete_feature_env_handler(event, context):
    try:
        user = get_current_user(event)
        require_admin(user)

        path = event["pathParameters"]
        flag = path["flag"]
        env = path["env"]

        service = get_feature_service()
        service.remove_env(flag, env, actor="ADMIN")

        return success_response(
            data={"message": "Environment removed"},
            status_code=200,
        )
    except AppException as e:
        return error_response(e.message, e.status_code)

    except Exception:
        return error_response("Internal Server Error", 500)
