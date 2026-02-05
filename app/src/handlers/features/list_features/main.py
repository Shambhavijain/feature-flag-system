from dependency import (
    get_feature_service,
    get_current_user,
    require_admin,
)
from error_handling.responses import success_response
from utils.handler_decorator import error_handler

@error_handler
def list_features_handler(event, context):
    user = get_current_user(event)

    service = get_feature_service()
    features = service.list_features()

    return success_response([f.model_dump() for f in features])
