import json
from dependency import get_current_user, require_admin, get_feature_service
from dto.feature_dto import UpdateFeatureEnvDTO
from error_handling.responses import success_response, error_response
from error_handling.exceptions import AppException

def update_feature_env_handler(event, context):
    try:
        user = get_current_user(event)
        require_admin(user)

        path = event["pathParameters"]
        flag = path["flag"]
        env = path["env"]

        body = json.loads(event.get("body", "{}"))
        request_evaluate = UpdateFeatureEnvDTO(**body)

        service = get_feature_service()
        service.update_env(flag, env, request_evaluate, actor= "ADMIN")

        return success_response(
            data={"message": "Environment updated"},
            status_code=200,
        )
    except AppException as e:
        return error_response(e.message, e.status_code)    

    except Exception:
        return error_response("Internal Server Error", 500)
