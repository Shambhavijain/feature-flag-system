from dependency import get_current_user, require_admin, get_feature_service
from error_handling.responses import success_response
from utils.handler_decorator import lambda_handler_wrapper


@lambda_handler_wrapper
def delete_feature_handler(event, context):
    user = get_current_user(event)
    require_admin(user)

    flag = event["pathParameters"]["flag"]

    service = get_feature_service()
    service.delete_feature(flag, actor="ADMIN")

    return success_response(
        data={"message": "Feature deleted"},
        status_code=200,
    )
