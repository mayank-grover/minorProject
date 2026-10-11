class ProjectError(Exception):
    def __init__(self, code, message, status=502, retryable=False):
        self.code, self.message, self.status, self.retryable = code, message, status, retryable
        super().__init__(message)
