class ValidationError(Exception):
    code = "VALIDATION_ERROR"
    message = "Invalid request payload."

    def __init__(self):
        super().__init__(self.message)
