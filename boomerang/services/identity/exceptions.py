class ValidationError(Exception):
    pass


class AuthError(Exception):
    code = "AUTH_ERROR"
    message = "Authentication required or invalid."


class RateLimitError(Exception):
    code = "RATE_LIMIT_ERROR"
    message = "Too many requests. Please try again later."


class DependencyError(Exception):
    pass
