class DomainError(Exception):
    code = "DOMAIN_ERROR"


class ResourceNotFoundError(DomainError):
    code = "RESOURCE_NOT_FOUND"


class ValidationFailedError(DomainError):
    code = "VALIDATION_FAILED"
