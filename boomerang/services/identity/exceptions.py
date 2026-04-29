class ValidationError(Exception):
    code = "VALIDATION_ERROR"
    message = "Invalid request payload."

    def __init__(self, message: str = None):
        if message is None:
            message = self.message
        super().__init__(message)


class AuthError(Exception):
    code = "AUTH_ERROR"
    message = "Authentication required or invalid."


class RateLimitError(Exception):
    code = "RATE_LIMIT_ERROR"
    message = "Too many requests. Please try again later."


class DependencyError(Exception):
    pass
