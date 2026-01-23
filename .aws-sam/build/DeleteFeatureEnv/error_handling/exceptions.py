class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationException(AppException):
    def __init__(self, message: str):
        super().__init__(message, 400)


class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(message, 409)


class UnauthorizedException(AppException):
    def __init__(self, message="Unauthorized"):
        super().__init__(message, 401)



class FeatureAlreadyExistsException(AppException):
    def __init__(self):
        super().__init__("Feature already exists", 409)
