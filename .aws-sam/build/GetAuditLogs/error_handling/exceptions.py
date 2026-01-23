class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class RepositoryException(AppException):
    def __init__(self, message="Data access error"):
        super().__init__(message, 500)

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

class NotFoundException(AppException):
    def __init__(self, message: str):
        super().__init__(message, 404)


class FeatureNotFoundException(NotFoundException):
    def __init__(self, feature_name: str):
        super().__init__(f"Feature '{feature_name}' not found")


class EnvironmentNotFoundException(NotFoundException):
    def __init__(self, feature_name: str, environment: str):
        super().__init__(
            f"Environment '{environment}' not configured for feature '{feature_name}'"
        )
