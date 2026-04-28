class ValidationError(Exception):
    pass


class AuthError(Exception):
    pass


class RateLimitError(Exception):
    pass


class DependencyError(Exception):
    pass
