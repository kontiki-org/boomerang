class ValidationError(Exception):
    """Raised when the HTTP payload or configuration is invalid."""


class ProviderError(Exception):
    """Raised when the underlying email provider fails."""
