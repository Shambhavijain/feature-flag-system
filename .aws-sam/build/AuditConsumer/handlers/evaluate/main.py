import json
from dependency import get_current_user, get_feature_service
from dto.feature_dto import EvaluateDTO
from error_handling.responses import success_response, error_response

def evaluate_feature_handler(event, context):
    try:
        get_current_user(event)  

        body = json.loads(event.get("body", "{}"))
        dto = EvaluateDTO(**body)

        service = get_feature_service()
        enabled = service.evaluate(dto)

        return success_response(
            data={"enabled": enabled},
            status_code=200,
        )

    except Exception as e:
        return error_response(str(e), 400)
