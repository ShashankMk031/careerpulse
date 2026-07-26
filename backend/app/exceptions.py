class AppException(Exception):
    """Base application exception for CareerPulse REST API."""
    def __init__(self, message: str, error_code: str = "INTERNAL_SERVER_ERROR"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

class ValidationException(AppException):
    """Raised when request query parameters or request body fail validation validations."""
    def __init__(self, message: str, error_code: str = "BAD_REQUEST"):
        super().__init__(message, error_code)

class NotFoundException(AppException):
    """Raised when a requested resource (e.g. company, skill) does not exist."""
    def __init__(self, message: str, error_code: str = "RESOURCE_NOT_FOUND"):
        super().__init__(message, error_code)

class DatabaseException(AppException):
    """Raised on serving database failures during read/write operations."""
    def __init__(self, message: str, error_code: str = "DATABASE_ERROR"):
        super().__init__(message, error_code)
