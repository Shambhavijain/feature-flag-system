import json
from dependency import get_current_user, require_admin, get_feature_service
from dto.feature_dto import CreateFeatureDTO
from error_handling.responses import success_response, error_response
from error_handling.exceptions import AppException

def create_feature_handler(event, context):
    try:
        user = get_current_user(event)
        require_admin(user)

        body = json.loads(event.get("body", "{}"))
        dto = CreateFeatureDTO(**body)

        service = get_feature_service()
        service.create_feature(dto, actor="ADMIN")

        return success_response(
            data={"message": "Feature Created"},
            status_code=201,
        )

    except AppException as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Internal Server Error", 500)
