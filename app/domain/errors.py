class DomainError(Exception):
    code = "DOMAIN_ERROR"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code


class ResourceNotFoundError(DomainError):
    code = "RESOURCE_NOT_FOUND"

    def __init__(self, message: str = "Resource not found", entity: str = "", entity_id: str = ""):
        msg = message or f"{entity} with id {entity_id} not found"
        super().__init__(msg)


class ValidationFailedError(DomainError):
    code = "VALIDATION_FAILED"

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message)


class ResourceConflictError(DomainError):
    code = "RESOURCE_CONFLICT"

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message)
