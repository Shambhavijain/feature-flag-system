import logging
from functools import wraps
from json import JSONDecodeError
from pydantic import ValidationError

from error_handling.responses import error_response
from error_handling.exceptions import AppException

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def error_handler(func):
    @wraps(func)
    def wrapper(event, context):
        try:
            return func(event, context)

        except JSONDecodeError:
            return error_response("Invalid JSON body", 400)

        except ValidationError as e:
            return error_response(e.errors(), 400)

        except AppException as e:
            logger.info(
                f"Handled AppException | "
                f"status={e.status_code} | message={e.message}"
            )
            return error_response(e.message, e.status_code)

        except Exception as e:
            logger.exception("Unhandled exception in lambda handler", exc_info=e)
            return error_response("Internal Server Error", 500)

    return wrapper
