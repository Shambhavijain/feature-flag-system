from dependency import get_current_user, require_admin, get_feature_service
from error_handling.responses import success_response
from utils.handler_decorator import lambda_handler_wrapper


@lambda_handler_wrapper
def get_feature_audit_handler(event, context):
    user = get_current_user(event)
    require_admin(user)

    flag = event["pathParameters"]["flag"]

    service = get_feature_service()
    audits = service.get_audit_logs(flag)

    return success_response(data=audits, status_code=200)
