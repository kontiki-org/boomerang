class ValidationError(Exception):
    """Raised when the HTTP payload or configuration is invalid."""


class NotFoundError(Exception):
    """Raised when a resource does not exist."""


class ProviderError(Exception):
    """Raised when the underlying email provider fails."""
