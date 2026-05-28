# Error Handling

> How errors are handled in this project.

---

## Overview

<!--
Document your project's error handling conventions here.

Questions to answer:
- What error types do you define?
- How are errors propagated?
- How are errors logged?
- How are errors returned to clients?
-->

Backend returns consistent, machine-readable errors for all API endpoints.
Every error response must include:

- `error.code`
- `error.message`
- `request_id`

---

## Error Types

<!-- Custom error classes/types -->

- `DomainError`: business rule violations (not found, invalid state).
- `ValidationError`: request payload/parameter validation errors.
- `InfrastructureError`: provider/storage/network/database failures.
- `AuthorizationError`: authn/authz failures.

---

## Error Handling Patterns

<!-- Try-catch patterns, error propagation -->

- Raise typed errors in `domain`/`application`, map them once in API layer.
- Avoid broad `except Exception` unless re-raising with context.
- Include `request_id` and stable `error.code` in logs and responses.
- For async indexing tasks, persist failure reason in job status payload.

---

## API Error Responses

<!-- Standard error response format -->

```json
{
  "error": {
    "code": "DOCUMENT_PARSE_FAILED",
    "message": "Failed to parse document with supported parser set"
  },
  "request_id": "req_12345"
}
```

Status code mapping:

- 400: invalid parameter / payload
- 401/403: authentication / authorization
- 404: resource not found
- 409: conflict (duplicate upload/checksum)
- 422: domain rule violation
- 500/503: internal or downstream dependency failure

---

## Common Mistakes

<!-- Error handling mistakes your team has made -->

- Returning raw Python exception messages to clients.
- Using ad-hoc error strings without stable `error.code`.
- Logging stack traces for expected validation failures as `error`.
- Swallowing exceptions in Celery task retries without job status update.
