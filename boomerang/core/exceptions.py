class AuthError(Exception):
    code = "AUTH_ERROR"
    message = "Authentication required or invalid."

    def __init__(self):
        super().__init__(self.message)


class NotFoundError(Exception):
    code = "NOT_FOUND_ERROR"
    message = "Resource not found."

    def __init__(self):
        super().__init__(self.message)


class ValidationError(Exception):
    code = "VALIDATION_ERROR"
    message = "Invalid request payload."

    def __init__(self):
        super().__init__(self.message)
