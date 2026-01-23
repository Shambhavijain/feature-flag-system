import logging
from functools import wraps

from error_handling.responses import error_response
from error_handling.exceptions import AppException


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler_wrapper(func):
    @wraps(func)
    def wrapper(event, context):
        try:
            return func(event, context)

        except AppException as e:
            logger.info(
                f"Handled AppException | "
                f"status={e.status_code} | message={e.message}"
            )
            return error_response(e.message, e.status_code)

        except Exception as e:
            logger.exception(
                "Unhandled exception in lambda handler",
                exc_info=e
            )
            return error_response("Internal Server Error", 500)

    return wrapper
