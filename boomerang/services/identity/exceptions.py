class ValidationError(Exception):
    code = "VALIDATION_ERROR"
    message = "Invalid request payload."

    def __init__(self):
        super().__init__(self.message)


class AuthError(Exception):
    code = "AUTH_ERROR"
    message = "Authentication required or invalid."

    def __init__(self):
        super().__init__(self.message)


class RateLimitError(Exception):
    code = "RATE_LIMIT_ERROR"
    message = "Too many requests. Please try again later."

    def __init__(self):
        super().__init__(self.message)


class DependencyError(Exception):
    code = "DEPENDENCY_ERROR"
    message = "Temporary service dependency failure."

    def __init__(self):
        super().__init__(self.message)
